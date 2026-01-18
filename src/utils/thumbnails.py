"""
Thumbnail generation utilities for video clips.

Usage:
    python src/utils/thumbnails.py --dir clips/
    python src/utils/thumbnails.py --file clips/some_clip.mp4
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Get project root and FFmpeg path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFMPEG_PATH = os.path.join(PROJECT_ROOT, "tools", "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")
FFPROBE_PATH = os.path.join(PROJECT_ROOT, "tools", "ffmpeg-master-latest-win64-gpl", "bin", "ffprobe.exe")


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds, or None on failure
    """
    if not os.path.exists(video_path):
        return None

    cmd = [
        FFPROBE_PATH,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
        return None

    except (subprocess.TimeoutExpired, ValueError, Exception):
        return None


def generate_thumbnail(
    video_path: str,
    output_path: Optional[str] = None,
    timestamp_percent: float = 0.3
) -> Optional[str]:
    """
    Generate a thumbnail from a video file.

    Uses FFmpeg to extract a frame from the video at the specified
    percentage of the video duration.

    Args:
        video_path: Path to the video file
        output_path: Path for the output thumbnail (default: same name with .jpg)
        timestamp_percent: Position in video to extract frame (0.0 to 1.0, default 0.3 = 30%)

    Returns:
        Path to the generated thumbnail, or None on failure
    """
    if not os.path.exists(video_path):
        print(f"[thumbnail] Video not found: {video_path}")
        return None

    # Determine output path
    if output_path is None:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(video_dir, f"{video_name}.jpg")

    # Get video duration
    duration = get_video_duration(video_path)
    if duration is None:
        print(f"[thumbnail] Could not get duration for: {video_path}")
        return None

    # Calculate timestamp
    timestamp = duration * timestamp_percent

    # Build FFmpeg command
    cmd = [
        FFMPEG_PATH,
        '-y',                          # Overwrite output
        '-ss', str(timestamp),         # Seek to timestamp
        '-i', video_path,              # Input file
        '-vframes', '1',               # Extract 1 frame
        '-q:v', '2',                   # JPEG quality (2 = high quality)
        output_path
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and os.path.exists(output_path):
            size_kb = os.path.getsize(output_path) / 1024
            print(f"[thumbnail] Created: {os.path.basename(output_path)} ({size_kb:.1f} KB)")
            return output_path
        else:
            error_msg = result.stderr[:200] if result.stderr else 'Unknown error'
            print(f"[thumbnail] FFmpeg failed: {error_msg}")
            return None

    except subprocess.TimeoutExpired:
        print(f"[thumbnail] FFmpeg timed out for: {video_path}")
        return None
    except Exception as e:
        print(f"[thumbnail] Error: {e}")
        return None


def generate_thumbnails_for_dir(clips_dir: str) -> int:
    """
    Generate thumbnails for all .mp4 files in a directory that don't have them.

    Scans for .mp4 files without corresponding .jpg thumbnails and
    generates missing thumbnails.

    Args:
        clips_dir: Directory containing video clips

    Returns:
        Number of thumbnails generated
    """
    if not os.path.exists(clips_dir):
        print(f"[thumbnail] Directory not found: {clips_dir}")
        return 0

    generated_count = 0

    # Find all .mp4 files
    for filename in os.listdir(clips_dir):
        if not filename.lower().endswith('.mp4'):
            continue

        video_path = os.path.join(clips_dir, filename)
        video_name = os.path.splitext(filename)[0]
        thumbnail_path = os.path.join(clips_dir, f"{video_name}.jpg")

        # Skip if thumbnail already exists
        if os.path.exists(thumbnail_path):
            continue

        # Generate thumbnail
        result = generate_thumbnail(video_path, thumbnail_path)
        if result:
            generated_count += 1

    return generated_count


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnails for video clips")
    parser.add_argument(
        "--dir", "-d",
        help="Directory containing video clips"
    )
    parser.add_argument(
        "--file", "-f",
        help="Single video file to generate thumbnail for"
    )
    parser.add_argument(
        "--timestamp", "-t",
        type=float,
        default=0.3,
        help="Position in video to extract frame (0.0 to 1.0, default: 0.3)"
    )
    args = parser.parse_args()

    if not args.dir and not args.file:
        parser.print_help()
        print("\nError: Must specify either --dir or --file")
        sys.exit(1)

    # Single file mode
    if args.file:
        result = generate_thumbnail(args.file, timestamp_percent=args.timestamp)
        if result:
            print(f"Thumbnail saved: {result}")
        else:
            print("Failed to generate thumbnail")
            sys.exit(1)

    # Directory mode
    if args.dir:
        count = generate_thumbnails_for_dir(args.dir)
        print(f"Generated {count} thumbnail(s)")


if __name__ == "__main__":
    main()
