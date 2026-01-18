"""
Stream recorder for capturing Kick livestreams using streamlink.

Usage:
    python src/recorder/stream_recorder.py --streamer clavicular

This script:
1. Polls the Kick API until the stream goes live
2. Starts a streamlink subprocess to record the stream
3. Monitors file size growth to detect recording health
4. Gracefully handles Ctrl+C to stop recording and cleanup
"""

import argparse
import requests
import time
import signal
import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import (
    KICK_API_BASE,
    RECORDINGS_DIR,
    DEFAULT_STREAMER,
    RECORDER_POLL_INTERVAL,
    RECORDER_HEALTH_INTERVAL,
    MIN_GROWTH_RATE_MB,
)
from src.db.schema import init_db, start_session, end_session, update_session_recording


class StreamRecorder:
    def __init__(self, streamer: str, session_id: int = None):
        self.streamer = streamer
        self.session_id = session_id
        self.api_url = f"{KICK_API_BASE}/{streamer}"
        self.running = False
        self.recording_process = None
        self.recording_path = None
        self.last_file_size = 0
        self.last_health_check = time.time()

        # Headers to avoid 403 blocks
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://kick.com/',
        }

    def get_stream_data(self) -> dict:
        """Fetch current stream data from Kick API."""
        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def is_stream_live(self) -> bool:
        """Check if the stream is currently live."""
        data = self.get_stream_data()
        if not data:
            return False

        livestream = data.get('livestream')
        return livestream and livestream.get('is_live', False)

    def get_file_size_mb(self, filepath: str) -> float:
        """Get file size in MB."""
        if not os.path.exists(filepath):
            return 0
        return os.path.getsize(filepath) / (1024 * 1024)

    def check_recording_health(self):
        """Check if recording is healthy by monitoring file size growth."""
        if not self.recording_path or not os.path.exists(self.recording_path):
            return

        current_time = time.time()
        elapsed_since_check = current_time - self.last_health_check

        if elapsed_since_check < RECORDER_HEALTH_INTERVAL:
            return

        current_size = self.get_file_size_mb(self.recording_path)
        size_growth = current_size - self.last_file_size
        growth_rate_per_minute = (size_growth / elapsed_since_check) * 60

        status = f"[{datetime.now().strftime('%H:%M:%S')}] "
        status += f"File: {current_size:.1f}MB | "
        status += f"Growth rate: {growth_rate_per_minute:.2f}MB/min"

        if growth_rate_per_minute < MIN_GROWTH_RATE_MB:
            status += " [WARNING: Low growth rate]"
            print(status)
        else:
            print(status)

        self.last_file_size = current_size
        self.last_health_check = current_time

    def start_recording(self):
        """Start streamlink subprocess to record the stream."""
        # Ensure recordings directory exists
        os.makedirs(RECORDINGS_DIR, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.streamer}_{timestamp}.mp4"
        self.recording_path = os.path.join(RECORDINGS_DIR, filename)

        # Build streamlink command
        url = f"https://kick.com/{self.streamer}"
        cmd = [
            "streamlink",
            url,
            "best",
            "-o",
            self.recording_path
        ]

        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting recording...")
            print(f"URL: {url}")
            print(f"Quality: best")
            print(f"Output: {self.recording_path}")
            print("-" * 50)

            self.recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Update session with recording path
            if self.session_id:
                update_session_recording(self.session_id, self.recording_path)

            self.last_file_size = 0
            self.last_health_check = time.time()

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Recording started (PID: {self.recording_process.pid})")

        except FileNotFoundError:
            print("[ERROR] streamlink not found. Please install streamlink:")
            print("  pip install streamlink")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to start recording: {e}")
            sys.exit(1)

    def stop_recording(self):
        """Stop the recording process gracefully."""
        if not self.recording_process:
            return

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stopping recording...")

        try:
            # Send SIGTERM to gracefully stop streamlink
            self.recording_process.terminate()
            self.recording_process.wait(timeout=10)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Recording stopped.")
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown takes too long
            print("[WARNING] Forcing shutdown...")
            self.recording_process.kill()
            self.recording_process.wait()
            print("[WARNING] Recording forcefully terminated.")

        self.recording_process = None

    def is_recording(self) -> bool:
        """Check if the recording process is still running."""
        if not self.recording_process:
            return False
        return self.recording_process.poll() is None

    def run(self):
        """Main recording loop."""
        print(f"\nStarting recorder for {self.streamer}...")
        print(f"Poll interval: {RECORDER_POLL_INTERVAL}s")
        print(f"Health check interval: {RECORDER_HEALTH_INTERVAL}s")
        print("-" * 50)

        # Initialize database
        init_db()

        self.running = True
        recording = False
        waiting_for_live = True

        while self.running:
            # Check if stream is live
            is_live = self.is_stream_live()

            if not is_live:
                if recording:
                    # Stream went offline, stop recording
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stream went offline.")
                    self.stop_recording()
                    recording = False

                    if self.session_id:
                        end_session(self.session_id)
                        print(f"Session {self.session_id} ended.")
                    self.session_id = None

                waiting_for_live = True

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {self.streamer} to go live...", end='\r')
                time.sleep(RECORDER_POLL_INTERVAL)
                continue

            # Stream is live
            if waiting_for_live:
                # Stream just went live
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {self.streamer} is LIVE!")

                # Start a new session if not provided
                if not self.session_id:
                    self.session_id = start_session(self.streamer)
                    print(f"Started session {self.session_id}")

                self.start_recording()
                recording = True
                waiting_for_live = False
                print("-" * 50)

            # If recording, check health and monitor
            if recording:
                if not self.is_recording():
                    # Recording process died unexpectedly
                    print(f"\n[ERROR] Recording process terminated unexpectedly!")
                    print(f"Recording PID {self.recording_process.pid if self.recording_process else 'unknown'} is no longer running.")
                    recording = False
                    if self.session_id:
                        end_session(self.session_id)
                        print(f"Session {self.session_id} ended.")
                    self.session_id = None
                else:
                    # Monitor file size growth
                    self.check_recording_health()

            time.sleep(RECORDER_POLL_INTERVAL)

    def stop(self):
        """Stop the recorder gracefully."""
        print("\n\nStopping recorder...")
        self.running = False

        if self.recording_process:
            self.stop_recording()

        if self.session_id:
            end_session(self.session_id)
            print(f"Session {self.session_id} ended.")


def main():
    parser = argparse.ArgumentParser(description="Record Kick streams with streamlink")
    parser.add_argument(
        "--streamer", "-s",
        default=DEFAULT_STREAMER,
        help=f"Streamer username (default: {DEFAULT_STREAMER})"
    )
    parser.add_argument(
        "--session",
        type=int,
        default=None,
        help="Existing session ID to attach recording to (optional)"
    )
    args = parser.parse_args()

    recorder = StreamRecorder(args.streamer, session_id=args.session)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        recorder.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        recorder.run()
    except KeyboardInterrupt:
        recorder.stop()


if __name__ == "__main__":
    main()
