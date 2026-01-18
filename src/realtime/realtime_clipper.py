"""
Real-time clipper - captures stream segments and creates clips instantly.

Usage:
    # Single streamer (from config)
    python src/realtime/realtime_clipper.py

    # Single streamer (CLI override)
    python src/realtime/realtime_clipper.py -s ninja

    # Multi-streamer mode (all streamers from config)
    python src/realtime/realtime_clipper.py --multi

    # List configured streamers
    python src/realtime/realtime_clipper.py --list

Configure streamers in config/streamers.json:
    {"streamers": ["clavicular", "ninja", "xqc"]}

This combines:
- Segment recording (streamlink + ffmpeg)
- Multi-trigger detection (viewer spikes, chat velocity, keywords)
- Instant clip creation (concat recent segments)
"""

import argparse
import subprocess
import os
import sys
import time
import signal
import glob
import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Get project root and FFmpeg path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_PATH = os.path.join(PROJECT_ROOT, "tools", "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")

from config.settings import (
    DEFAULT_STREAMER,
    CLIPS_DIR,
    CLIP_BEFORE,
    CLIP_AFTER,
    SEGMENT_DURATION,
    SEGMENTS_TO_KEEP,
    SEGMENTS_DIR,
    CLIP_COOLDOWN,
    MAX_CLIPS_PER_DAY,
    HIGH_PRIORITY_CONFIDENCE
)
from src.db.schema import init_db, start_session, end_session, log_moment
from src.realtime.triggers import ViewerTrigger, ChatTrigger, TriggerEvent
from src.utils.cleanup import cleanup_old_segments
from src.utils.thumbnails import generate_thumbnail


def load_streamers() -> List[str]:
    """Load streamers from config file."""
    config_path = os.path.join(PROJECT_ROOT, "config", "streamers.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
            return config.get("streamers", [DEFAULT_STREAMER])
    return [DEFAULT_STREAMER]


class SegmentRecorder:
    """
    Records stream in segments using streamlink + ffmpeg.
    Maintains a rolling buffer of recent segments.
    """

    def __init__(self, streamer: str, segments_dir: str = SEGMENTS_DIR):
        self.streamer = streamer
        # Use per-streamer directory
        self.segments_dir = os.path.join(segments_dir, streamer)
        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.segment_count = 0

        # Ensure segments directory exists
        os.makedirs(self.segments_dir, exist_ok=True)

    def start(self):
        """Start recording stream in segments."""
        self.running = True
        self._cleanup_old_segments()

        stream_url = f"https://kick.com/{self.streamer}"

        # Use forward slashes for FFmpeg compatibility
        segment_pattern = self.segments_dir.replace("\\", "/") + "/chunk_%04d.ts"

        print(f"[recorder] Starting segment recording for {self.streamer}")
        print(f"[recorder] Segment duration: {SEGMENT_DURATION}s, keeping last {SEGMENTS_TO_KEEP}")
        print(f"[recorder] Segment pattern: {segment_pattern}")

        try:
            # Step 1: Get the actual stream URL from streamlink
            print("[recorder] Getting stream URL...")
            result = subprocess.run(
                ['python', '-m', 'streamlink', stream_url, 'best', '--stream-url'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 or not result.stdout.strip():
                print(f"[recorder] Failed to get stream URL: {result.stderr}")
                self.running = False
                return

            hls_url = result.stdout.strip()
            print(f"[recorder] Got HLS URL")

            # Step 2: Use FFmpeg directly with the HLS URL
            # Use local FFmpeg from tools folder
            ffmpeg_path = FFMPEG_PATH.replace("\\", "/")
            cmd = f'"{ffmpeg_path}" -i "{hls_url}" -c copy -f segment -segment_time {SEGMENT_DURATION} -segment_format mpegts -reset_timestamps 1 -y "{segment_pattern}"'

            print(f"[recorder] Running: ffmpeg -i [URL] -c copy -f segment ... {segment_pattern}")
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Project root
            )
            print(f"[recorder] FFmpeg started (PID: {self.process.pid})")

            # Monitor for new segments in background
            monitor_thread = threading.Thread(target=self._monitor_segments, daemon=True)
            monitor_thread.start()

        except subprocess.TimeoutExpired:
            print("[recorder] Timeout getting stream URL")
            self.running = False
        except Exception as e:
            print(f"[recorder] Failed to start: {e}")
            self.running = False

    def _monitor_segments(self):
        """Monitor segments directory and cleanup old segments."""
        last_count = 0
        no_segment_count = 0

        while self.running:
            # Check if FFmpeg is still running
            if self.process and self.process.poll() is not None:
                print(f"[recorder] FFmpeg exited with code {self.process.returncode}")
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                if stderr:
                    print(f"[recorder] FFmpeg error: {stderr[:500]}")
                self.running = False
                break

            segments = self.get_segments()
            current_count = len(segments)

            if current_count > last_count:
                new_segments = current_count - last_count
                print(f"[recorder] +{new_segments} segment(s) | Total: {current_count} | Buffer: {current_count * SEGMENT_DURATION}s")
                last_count = current_count
                no_segment_count = 0

                # Cleanup old segments
                if current_count > SEGMENTS_TO_KEEP:
                    self._cleanup_old_segments()
            else:
                no_segment_count += 1
                if no_segment_count > 5 and current_count == 0:
                    print(f"[recorder] No segments after {no_segment_count * 2}s - checking FFmpeg...")

            time.sleep(2)

    def _cleanup_old_segments(self):
        """Remove old segments beyond the buffer limit."""
        segments = self.get_segments()
        if len(segments) > SEGMENTS_TO_KEEP:
            to_remove = segments[:-SEGMENTS_TO_KEEP]
            for seg in to_remove:
                try:
                    os.remove(seg)
                except OSError:
                    pass

    def get_segments(self) -> List[str]:
        """Get list of segment files, sorted by creation time."""
        pattern = os.path.join(self.segments_dir, "chunk_*.ts")
        segments = glob.glob(pattern)
        return sorted(segments, key=os.path.getmtime)

    def get_recent_segments(self, seconds: int = 60) -> List[str]:
        """Get segments covering the last N seconds."""
        num_segments = (seconds // SEGMENT_DURATION) + 1
        segments = self.get_segments()
        return segments[-num_segments:] if segments else []

    def stop(self):
        """Stop recording."""
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        print("[recorder] Stopped")

    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self.running and self.process and self.process.poll() is None


class ClipCreator:
    """Creates clips by concatenating segments."""

    def __init__(self, streamer: str, clips_dir: str = CLIPS_DIR):
        # Use per-streamer directory
        self.clips_dir = os.path.join(clips_dir, streamer)
        self.clip_count = 0
        os.makedirs(self.clips_dir, exist_ok=True)

    def create_clip(
        self,
        segments: List[str],
        trigger_event: TriggerEvent,
        streamer: str
    ) -> Optional[str]:
        """
        Create a clip from the given segments.

        Returns the path to the created clip, or None on failure.
        """
        if not segments:
            print("[clipper] No segments to clip")
            return None

        self.clip_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trigger_type = trigger_event.trigger_type
        filename = f"{streamer}_{trigger_type}_{timestamp}_{self.clip_count:03d}.mp4"
        output_path = os.path.join(self.clips_dir, filename)

        print(f"[clipper] Creating clip from {len(segments)} segments...")

        # Method 1: Concat protocol (fast, works for .ts files)
        concat_input = "|".join(segments)
        cmd = [
            FFMPEG_PATH,
            '-y',
            '-i', f'concat:{concat_input}',
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            output_path
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"[clipper] Created: {filename} ({size_mb:.1f} MB)")

                # Generate thumbnail for the clip
                thumbnail_path = generate_thumbnail(output_path)
                if thumbnail_path:
                    print(f"[clipper] Thumbnail: {os.path.basename(thumbnail_path)}")

                return output_path
            else:
                print(f"[clipper] FFmpeg failed: {result.stderr[:200] if result.stderr else 'Unknown error'}")
                return None

        except subprocess.TimeoutExpired:
            print("[clipper] FFmpeg timed out")
            return None
        except Exception as e:
            print(f"[clipper] Error: {e}")
            return None


class RealtimeClipper:
    """
    Main orchestrator for real-time clipping.
    Coordinates recording, triggers, and clip creation.
    """

    def __init__(self, streamer: str):
        self.streamer = streamer
        self.running = False
        self.session_id: Optional[int] = None

        # Components (with per-streamer directories)
        self.recorder = SegmentRecorder(streamer)
        self.clip_creator = ClipCreator(streamer)

        # Triggers
        self.viewer_trigger: Optional[ViewerTrigger] = None
        self.chat_trigger: Optional[ChatTrigger] = None

        # Track clip times to prevent duplicates
        self.last_clip_time: Optional[datetime] = None
        self.clip_cooldown = CLIP_COOLDOWN  # seconds between clips (from settings)

        # Daily clip limit tracking
        self.clips_today = 0
        self.clip_date = datetime.now().date()

    def _on_trigger(self, event: TriggerEvent):
        """Callback when any trigger fires.

        All triggers are logged for visibility, but clips are only created
        when cooldown has passed (unless high-priority).
        """
        # ALWAYS log the trigger event (no cooldown for logging)
        print(f"\n{'='*60}")
        print(f"  TRIGGER: {event.trigger_type.upper()}")
        print(f"  Confidence: {event.confidence:.2f}")
        print(f"  Data: {event.data}")
        print(f"{'='*60}\n")

        # Reset daily counter at midnight
        today = datetime.now().date()
        if today != self.clip_date:
            self.clip_date = today
            self.clips_today = 0
            print(f"[clip] New day - resetting clip counter")

        # Check daily limit
        if self.clips_today >= MAX_CLIPS_PER_DAY:
            print(f"[clip] Daily limit reached ({MAX_CLIPS_PER_DAY} clips) - skipping")
            return

        # Check if this is a high-priority trigger that can bypass cooldown
        is_high_priority = (
            event.confidence >= HIGH_PRIORITY_CONFIDENCE or
            event.trigger_type in ["combo", "super_combo", "hype_moment"] or
            (event.trigger_type == "viewer_spike" and event.data.get("ratio", 0) >= 3.0)
        )

        # Check cooldown for CLIP CREATION (bypassed for high-priority)
        if self.last_clip_time and not is_high_priority:
            elapsed = (datetime.now() - self.last_clip_time).total_seconds()
            if elapsed < self.clip_cooldown:
                print(f"[clip] Skipping clip creation (cooldown: {self.clip_cooldown - elapsed:.0f}s remaining)")
                return

        if is_high_priority and self.last_clip_time:
            elapsed = (datetime.now() - self.last_clip_time).total_seconds()
            if elapsed < self.clip_cooldown:
                print(f"[clip] HIGH PRIORITY trigger - bypassing cooldown!")

        # Get recent segments
        clip_duration = CLIP_BEFORE + CLIP_AFTER
        segments = self.recorder.get_recent_segments(clip_duration)

        if not segments:
            print("[main] No segments available for clipping")
            return

        # Create clip
        clip_path = self.clip_creator.create_clip(segments, event, self.streamer)

        if clip_path:
            self.last_clip_time = datetime.now()
            self.clips_today += 1
            print(f"[clip] Clips today: {self.clips_today}/{MAX_CLIPS_PER_DAY}")

            # Log to database
            if self.session_id:
                log_moment(
                    session_id=self.session_id,
                    stream_elapsed_seconds=0,  # Not tracking elapsed in realtime mode
                    viewer_count=event.data.get('viewer_count', 0),
                    baseline_viewers=event.data.get('baseline', 0),
                    spike_ratio=event.data.get('ratio', 0),
                    trigger_type=event.trigger_type,
                    trigger_data=str(event.data)
                )

    def run(self):
        """Main run loop."""
        print(f"\n{'='*60}")
        print(f"  REAL-TIME CLIPPER")
        print(f"  Streamer: {self.streamer}")
        print(f"{'='*60}\n")

        # Clean up old segment files from previous sessions
        cleanup_old_segments(SEGMENTS_DIR)

        # Initialize database
        init_db()
        self.session_id = start_session(self.streamer)
        print(f"[main] Started session {self.session_id}")

        self.running = True

        # Start viewer trigger (also gets chatroom ID)
        self.viewer_trigger = ViewerTrigger(self.streamer, callback=self._on_trigger)
        self.viewer_trigger.start_threaded()

        # Wait for viewer trigger to get chatroom ID
        print("[main] Waiting for stream info...")
        for _ in range(30):  # Wait up to 30 seconds
            chatroom_id = self.viewer_trigger.get_chatroom_id()
            if chatroom_id:
                break
            time.sleep(1)

        # Start chat trigger if we have chatroom ID
        if chatroom_id:
            print(f"[main] Starting chat monitor (chatroom {chatroom_id})")
            self.chat_trigger = ChatTrigger(chatroom_id, callback=self._on_trigger)
            self.chat_trigger.start_threaded()
        else:
            print("[main] Could not get chatroom ID - chat monitoring disabled")

        # Wait for stream to go live before recording
        print("[main] Waiting for stream to go live...")
        wait_count = 0
        while self.running and not self.viewer_trigger.is_live:
            wait_count += 1
            if wait_count % 5 == 0:
                print(f"[main] Still waiting for live stream... ({wait_count * 2}s)")
            time.sleep(2)

        if not self.running:
            return

        # Start recording
        print("[main] Stream is LIVE - starting recorder NOW")
        self.recorder.start()
        print("[main] Recorder started")

        # Main loop - just keep running
        try:
            while self.running:
                # Check if recording is still active
                if not self.recorder.is_recording():
                    print("[main] Recording stopped - attempting restart...")
                    time.sleep(5)
                    if self.viewer_trigger.is_live:
                        self.recorder.start()

                time.sleep(5)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop all components."""
        print("\n[main] Shutting down...")
        self.running = False

        if self.recorder:
            self.recorder.stop()
        if self.viewer_trigger:
            self.viewer_trigger.stop()
        if self.chat_trigger:
            self.chat_trigger.stop()

        if self.session_id:
            end_session(self.session_id)
            print(f"[main] Session {self.session_id} ended")

        print("[main] Goodbye!")


class MultiStreamerClipper:
    """
    Manages multiple RealtimeClippers for different streamers.
    Each streamer runs in its own thread with independent triggers and recording.
    """

    def __init__(self, streamers: List[str]):
        self.streamers = streamers
        self.clippers: Dict[str, RealtimeClipper] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self.running = False

    def start(self):
        """Start clippers for all streamers."""
        print(f"\n{'='*60}")
        print(f"  MULTI-STREAMER CLIPPER")
        print(f"  Monitoring {len(self.streamers)} streamer(s):")
        for s in self.streamers:
            print(f"    - {s}")
        print(f"{'='*60}\n")

        self.running = True

        for streamer in self.streamers:
            clipper = RealtimeClipper(streamer)
            thread = threading.Thread(target=clipper.run, daemon=True, name=f"clipper-{streamer}")
            self.clippers[streamer] = clipper
            self.threads[streamer] = thread
            thread.start()
            print(f"[multi] Started clipper thread for {streamer}")
            time.sleep(2)  # Stagger starts to avoid API rate limits

        # Keep main thread alive
        try:
            while self.running:
                # Check thread health
                for streamer, thread in self.threads.items():
                    if not thread.is_alive():
                        print(f"[multi] WARNING: Thread for {streamer} died!")
                time.sleep(10)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop all clippers."""
        print("\n[multi] Stopping all clippers...")
        self.running = False
        for streamer, clipper in self.clippers.items():
            print(f"[multi] Stopping {streamer}...")
            clipper.stop()
        print("[multi] All clippers stopped. Goodbye!")


def main():
    parser = argparse.ArgumentParser(description="Real-time stream clipper")
    parser.add_argument(
        "--streamer", "-s",
        help="Single streamer username (overrides config file)"
    )
    parser.add_argument(
        "--multi", "-m",
        action="store_true",
        help="Multi-streamer mode: monitor all streamers from config/streamers.json"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List configured streamers and exit"
    )
    args = parser.parse_args()

    # List mode
    if args.list:
        streamers = load_streamers()
        print("Configured streamers:")
        for s in streamers:
            print(f"  - {s}")
        return

    # Multi-streamer mode
    if args.multi:
        streamers = load_streamers()
        if not streamers:
            print("No streamers configured. Add streamers to config/streamers.json")
            return

        multi = MultiStreamerClipper(streamers)

        def signal_handler(sig, frame):
            multi.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        multi.start()

    # Single streamer mode
    else:
        if args.streamer:
            streamer = args.streamer
        else:
            # Use first streamer from config, or default
            streamers = load_streamers()
            streamer = streamers[0] if streamers else DEFAULT_STREAMER

        clipper = RealtimeClipper(streamer)

        def signal_handler(sig, frame):
            clipper.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        clipper.run()


if __name__ == "__main__":
    main()
