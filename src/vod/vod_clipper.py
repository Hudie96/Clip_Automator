"""
VOD Clipper - Downloads and clips segments from Kick VODs using FFmpeg.

Supports:
- Fetching VOD list for a streamer
- Creating clips from VODs with start/end timestamps
- Streaming download (doesn't download entire VOD)
"""

import os
import subprocess
import requests
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Get project root and FFmpeg path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FFMPEG_PATH = PROJECT_ROOT / "tools" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"
CLIPS_DIR = PROJECT_ROOT / "clips"


@dataclass
class VODInfo:
    """Information about a VOD."""
    id: str
    title: str
    duration: int  # seconds
    created_at: str
    thumbnail_url: str
    views: int
    streamer: str
    source_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'duration': self.duration,
            'duration_display': self._format_duration(),
            'created_at': self.created_at,
            'thumbnail_url': self.thumbnail_url,
            'views': self.views,
            'streamer': self.streamer,
        }

    def _format_duration(self) -> str:
        """Format duration as HH:MM:SS."""
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


class VODClipper:
    """
    Handles VOD listing and clipping from Kick.

    Usage:
        clipper = VODClipper()
        vods = clipper.get_vod_list("streamer_name")
        clip_path = clipper.create_clip(vod_id, start_seconds=3600, end_seconds=3660)
    """

    KICK_API_BASE = "https://kick.com/api/v2"

    def __init__(self, clips_dir: Optional[Path] = None):
        self.clips_dir = clips_dir or CLIPS_DIR
        self.clips_dir.mkdir(parents=True, exist_ok=True)

    def get_vod_list(self, streamer: str, limit: int = 20) -> List[VODInfo]:
        """
        Fetch the list of VODs for a streamer.

        Args:
            streamer: The streamer's username
            limit: Maximum number of VODs to return

        Returns:
            List of VODInfo objects
        """
        url = f"{self.KICK_API_BASE}/channels/{streamer}/videos"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            vods = []
            for video in data[:limit]:
                vod = VODInfo(
                    id=str(video.get('id', '')),
                    title=video.get('session_title', 'Untitled'),
                    duration=video.get('duration', 0) or self._parse_duration_from_length(video),
                    created_at=video.get('created_at', ''),
                    thumbnail_url=video.get('thumbnail', {}).get('src', '') if isinstance(video.get('thumbnail'), dict) else video.get('thumbnail', ''),
                    views=video.get('views', 0),
                    streamer=streamer,
                    source_url=video.get('source', None)
                )
                vods.append(vod)

            return vods

        except requests.RequestException as e:
            print(f"[vod] Error fetching VODs for {streamer}: {e}")
            return []

    def _parse_duration_from_length(self, video: dict) -> int:
        """Parse duration from video length field if duration is missing."""
        length = video.get('video', {}).get('uuid', '')
        # Try to extract duration from other fields
        duration_str = video.get('livestream', {}).get('duration', 0)
        if isinstance(duration_str, int):
            return duration_str
        return 0

    def get_vod_details(self, vod_id: str) -> Optional[VODInfo]:
        """
        Get detailed information about a specific VOD.

        Args:
            vod_id: The VOD ID

        Returns:
            VODInfo object or None if not found
        """
        url = f"{self.KICK_API_BASE}/video/{vod_id}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            video = response.json()

            # Extract streamer from the response
            streamer = video.get('livestream', {}).get('channel', {}).get('slug', 'unknown')

            return VODInfo(
                id=str(video.get('id', vod_id)),
                title=video.get('livestream', {}).get('session_title', 'Untitled'),
                duration=video.get('livestream', {}).get('duration', 0),
                created_at=video.get('created_at', ''),
                thumbnail_url=video.get('livestream', {}).get('thumbnail', ''),
                views=video.get('views', 0),
                streamer=streamer,
                source_url=video.get('source', None)
            )

        except requests.RequestException as e:
            print(f"[vod] Error fetching VOD {vod_id}: {e}")
            return None

    def _get_vod_stream_url(self, vod_id: str) -> Optional[str]:
        """
        Get the HLS stream URL for a VOD using streamlink.

        Args:
            vod_id: The VOD ID

        Returns:
            HLS URL or None if not found
        """
        # First try to get the source URL from the API
        vod_details = self.get_vod_details(vod_id)
        if vod_details and vod_details.source_url:
            return vod_details.source_url

        # Fallback: Try streamlink to get the VOD URL
        # Note: This may not work for all VODs
        vod_url = f"https://kick.com/video/{vod_id}"

        try:
            result = subprocess.run(
                ['python', '-m', 'streamlink', vod_url, 'best', '--stream-url'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

            print(f"[vod] Could not get stream URL via streamlink: {result.stderr}")
            return None

        except subprocess.TimeoutExpired:
            print("[vod] Timeout getting VOD stream URL")
            return None
        except Exception as e:
            print(f"[vod] Error getting VOD stream URL: {e}")
            return None

    def parse_timestamp(self, timestamp: str) -> int:
        """
        Parse a timestamp string to seconds.

        Supports formats:
        - HH:MM:SS (01:23:45)
        - MM:SS (23:45)
        - Seconds (1234)

        Args:
            timestamp: The timestamp string

        Returns:
            Total seconds
        """
        timestamp = timestamp.strip()

        # Already seconds
        if timestamp.isdigit():
            return int(timestamp)

        # Parse HH:MM:SS or MM:SS
        parts = timestamp.split(':')
        if len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        elif len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")

    def create_clip(
        self,
        vod_id: str,
        start_time: str,
        end_time: str,
        streamer: str = "unknown",
        output_name: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Optional[str]:
        """
        Create a clip from a VOD segment.

        This uses FFmpeg's stream copy with -ss before input for efficient seeking.
        Only downloads the required segment, not the entire VOD.

        Args:
            vod_id: The VOD ID
            start_time: Start timestamp (HH:MM:SS or seconds)
            end_time: End timestamp (HH:MM:SS or seconds)
            streamer: Streamer name for filename
            output_name: Optional custom output filename
            progress_callback: Optional callback for progress updates

        Returns:
            Path to the created clip, or None on failure
        """
        # Parse timestamps
        try:
            start_seconds = self.parse_timestamp(start_time) if isinstance(start_time, str) else start_time
            end_seconds = self.parse_timestamp(end_time) if isinstance(end_time, str) else end_time
        except ValueError as e:
            print(f"[vod] Invalid timestamp: {e}")
            return None

        if end_seconds <= start_seconds:
            print(f"[vod] End time must be after start time")
            return None

        duration = end_seconds - start_seconds

        # Get the VOD stream URL
        if progress_callback:
            progress_callback("Getting VOD URL...", 10)

        stream_url = self._get_vod_stream_url(vod_id)
        if not stream_url:
            print(f"[vod] Could not get stream URL for VOD {vod_id}")
            return None

        # Generate output filename
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{streamer}_vod_{vod_id}_{timestamp}.mp4"

        # Ensure .mp4 extension
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'

        # Create streamer-specific directory
        streamer_dir = self.clips_dir / streamer
        streamer_dir.mkdir(parents=True, exist_ok=True)
        output_path = streamer_dir / output_name

        if progress_callback:
            progress_callback("Starting clip creation...", 20)

        # Build FFmpeg command
        # -ss before -i enables fast seeking without decoding
        # -t specifies duration
        # -c copy does stream copy (fast, no re-encoding)
        ffmpeg_path = str(FFMPEG_PATH).replace("\\", "/")
        cmd = [
            ffmpeg_path,
            '-y',                       # Overwrite output
            '-ss', str(start_seconds),  # Seek to start (before input for fast seek)
            '-i', stream_url,           # Input URL
            '-t', str(duration),        # Duration
            '-c', 'copy',               # Stream copy (no re-encode)
            '-bsf:a', 'aac_adtstoasc',  # Fix AAC audio for MP4
            str(output_path)
        ]

        print(f"[vod] Creating clip: {output_name}")
        print(f"[vod] Start: {start_seconds}s, Duration: {duration}s")

        try:
            # Run FFmpeg with progress monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Wait for completion (with timeout based on duration)
            timeout = max(60, duration * 2)  # At least 60s, or 2x duration
            stdout, stderr = process.communicate(timeout=timeout)

            if process.returncode == 0 and output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"[vod] Clip created: {output_name} ({size_mb:.1f} MB)")

                if progress_callback:
                    progress_callback("Clip created!", 100)

                return str(output_path)
            else:
                print(f"[vod] FFmpeg failed: {stderr[:500] if stderr else 'Unknown error'}")
                return None

        except subprocess.TimeoutExpired:
            print(f"[vod] FFmpeg timed out after {timeout}s")
            process.kill()
            return None
        except Exception as e:
            print(f"[vod] Error creating clip: {e}")
            return None

    def format_seconds_to_timestamp(self, seconds: int) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # Test the VOD clipper
    clipper = VODClipper()

    # Test fetching VOD list
    print("Fetching VODs for 'clavicular'...")
    vods = clipper.get_vod_list("clavicular", limit=5)

    for vod in vods:
        print(f"  - {vod.title} ({vod._format_duration()}) - {vod.views} views")

    if vods:
        print(f"\nFirst VOD ID: {vods[0].id}")
