"""
Clip generator - creates video clips from detected moments.

Usage:
    python src/clip/create_clips.py --recording "recordings/clavicular_20260117.mp4"
    python src/clip/create_clips.py --session 1

This script:
1. Reads unprocessed moments from SQLite
2. Creates 60-second clips using FFmpeg
3. Marks moments as processed in the database
"""

import argparse
import subprocess
import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import (
    CLIP_BEFORE,
    CLIP_AFTER,
    CLIPS_DIR,
    RECORDINGS_DIR
)
from src.db.schema import (
    init_db,
    get_unprocessed_moments,
    mark_moment_processed,
    update_session_recording
)
from src.utils.timestamp import (
    seconds_to_ffmpeg_time,
    get_clip_window,
    generate_clip_filename,
    format_duration
)


def get_video_duration(video_path: str) -> float:
    """Get the duration of a video file using FFprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"[ERROR] Could not get video duration: {e}")
        return None


def create_clip(
    input_path: str,
    output_path: str,
    start_seconds: float,
    duration_seconds: float
) -> bool:
    """
    Create a clip using FFmpeg.

    Args:
        input_path: Path to the source video
        output_path: Path for the output clip
        start_seconds: Start time in seconds
        duration_seconds: Clip duration in seconds

    Returns:
        True if successful, False otherwise
    """
    start_time = seconds_to_ffmpeg_time(start_seconds)

    cmd = [
        'ffmpeg',
        '-y',                          # Overwrite output
        '-ss', start_time,             # Start time (before -i for fast seek)
        '-i', input_path,              # Input file
        '-t', str(duration_seconds),   # Duration
        '-c', 'copy',                  # Copy codecs (fast, no re-encoding)
        '-avoid_negative_ts', 'make_zero',
        output_path
    ]

    print(f"  Running: ffmpeg -ss {start_time} -i ... -t {duration_seconds} ...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] FFmpeg failed: {e.stderr[:200] if e.stderr else 'Unknown error'}")
        return False


def process_moments(recording_path: str = None, session_id: int = None, dry_run: bool = False):
    """
    Process all unprocessed moments and create clips.

    Args:
        recording_path: Override the recording path from database
        session_id: Only process moments from this session
        dry_run: If True, show what would be done without creating clips
    """
    # Ensure output directory exists
    os.makedirs(CLIPS_DIR, exist_ok=True)

    # Get moments to process
    moments = get_unprocessed_moments(session_id)

    if not moments:
        print("No unprocessed moments found.")
        return

    print(f"\nFound {len(moments)} unprocessed moment(s)")
    print("=" * 60)

    # Get video duration for bounds checking
    video_duration = None
    if recording_path and os.path.exists(recording_path):
        video_duration = get_video_duration(recording_path)
        if video_duration:
            print(f"Recording duration: {format_duration(video_duration)}")

    # Process each moment
    success_count = 0
    for moment in moments:
        moment_id = moment['id']
        elapsed = moment['stream_elapsed_seconds']
        viewers = moment['viewer_count']
        ratio = moment['spike_ratio']

        # Use provided recording path or fall back to database
        source_path = recording_path or moment.get('recording_path')

        if not source_path:
            print(f"\n[SKIP] Moment #{moment_id}: No recording path available")
            continue

        if not os.path.exists(source_path):
            print(f"\n[SKIP] Moment #{moment_id}: Recording not found at {source_path}")
            continue

        # Calculate clip window
        start, duration = get_clip_window(
            moment_seconds=elapsed,
            before=CLIP_BEFORE,
            after=CLIP_AFTER,
            max_duration=video_duration
        )

        # Generate output filename
        output_filename = generate_clip_filename(
            streamer=moment.get('streamer', 'clip'),
            moment_seconds=elapsed,
            moment_id=moment_id
        )
        output_path = os.path.join(CLIPS_DIR, output_filename)

        print(f"\nMoment #{moment_id}:")
        print(f"  Time in stream: {format_duration(elapsed)}")
        print(f"  Viewers: {viewers:,} ({ratio:.1f}x baseline)")
        print(f"  Clip: {format_duration(start)} - {format_duration(start + duration)} ({duration}s)")
        print(f"  Output: {output_filename}")

        if dry_run:
            print("  [DRY RUN] Would create clip")
            continue

        # Create the clip
        if create_clip(source_path, output_path, start, duration):
            mark_moment_processed(moment_id, output_path)
            print(f"  [OK] Created {output_filename}")
            success_count += 1
        else:
            print(f"  [FAILED] Could not create clip")

    print("\n" + "=" * 60)
    print(f"Processed {success_count}/{len(moments)} moments successfully")

    if success_count > 0:
        print(f"Clips saved to: {os.path.abspath(CLIPS_DIR)}")


def list_recordings():
    """List available recordings."""
    if not os.path.exists(RECORDINGS_DIR):
        print(f"Recordings directory not found: {RECORDINGS_DIR}")
        return

    recordings = list(Path(RECORDINGS_DIR).glob("*.mp4"))
    recordings.extend(Path(RECORDINGS_DIR).glob("*.mkv"))
    recordings.extend(Path(RECORDINGS_DIR).glob("*.ts"))

    if not recordings:
        print("No recordings found.")
        return

    print(f"\nAvailable recordings in {RECORDINGS_DIR}/:")
    print("-" * 60)
    for rec in sorted(recordings, key=lambda x: x.stat().st_mtime, reverse=True):
        size_mb = rec.stat().st_size / (1024 * 1024)
        print(f"  {rec.name} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Create clips from detected moments")
    parser.add_argument(
        "--recording", "-r",
        help="Path to the recording file"
    )
    parser.add_argument(
        "--session", "-s",
        type=int,
        help="Only process moments from this session ID"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without creating clips"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available recordings"
    )
    args = parser.parse_args()

    # Initialize database
    init_db()

    if args.list:
        list_recordings()
        return

    if not args.recording and not args.session:
        print("Specify --recording or --session, or use --list to see recordings")
        print("\nExamples:")
        print('  python create_clips.py --recording "recordings/clavicular_20260117.mp4"')
        print('  python create_clips.py --session 1')
        print('  python create_clips.py --list')
        return

    process_moments(
        recording_path=args.recording,
        session_id=args.session,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
