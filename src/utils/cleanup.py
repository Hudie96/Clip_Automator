"""
Cleanup utilities for managing old clips and temporary segment files.

Usage:
    # Delete clips older than 7 days
    python src/utils/cleanup.py --clips --days 7

    # Clean up all segment files
    python src/utils/cleanup.py --segments

    # Both
    python src/utils/cleanup.py --clips --segments --days 14
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import CLIPS_DIR, SEGMENTS_DIR


def cleanup_old_clips(clips_dir: str = CLIPS_DIR, max_age_days: int = 7) -> int:
    """
    Scan the clips directory (recursively for per-streamer folders) and
    delete .mp4 files older than max_age_days.

    Args:
        clips_dir: Path to the clips directory
        max_age_days: Maximum age in days before a clip is deleted

    Returns:
        Count of deleted files
    """
    if not os.path.exists(clips_dir):
        print(f"[cleanup] Clips directory not found: {clips_dir}")
        return 0

    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    cutoff_timestamp = cutoff_time.timestamp()
    deleted_count = 0

    print(f"[cleanup] Scanning for clips older than {max_age_days} days...")
    print(f"[cleanup] Cutoff date: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Walk through directory recursively (handles per-streamer subdirectories)
    for root, dirs, files in os.walk(clips_dir):
        for filename in files:
            if not filename.lower().endswith('.mp4'):
                continue

            filepath = os.path.join(root, filename)

            try:
                file_mtime = os.path.getmtime(filepath)

                if file_mtime < cutoff_timestamp:
                    file_age_days = (datetime.now().timestamp() - file_mtime) / 86400
                    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)

                    os.remove(filepath)
                    deleted_count += 1

                    # Get relative path for cleaner logging
                    rel_path = os.path.relpath(filepath, clips_dir)
                    print(f"[cleanup] Deleted: {rel_path} (age: {file_age_days:.1f} days, size: {file_size_mb:.1f} MB)")

            except OSError as e:
                print(f"[cleanup] Error deleting {filepath}: {e}")
            except Exception as e:
                print(f"[cleanup] Unexpected error for {filepath}: {e}")

    if deleted_count > 0:
        print(f"[cleanup] Deleted {deleted_count} old clip(s)")
    else:
        print("[cleanup] No old clips to delete")

    return deleted_count


def cleanup_old_segments(segments_dir: str = SEGMENTS_DIR) -> int:
    """
    Remove all segment files (they're temporary).
    Safe to call on startup.

    Args:
        segments_dir: Path to the segments directory

    Returns:
        Count of deleted files
    """
    if not os.path.exists(segments_dir):
        print(f"[cleanup] Segments directory not found: {segments_dir}")
        return 0

    deleted_count = 0
    total_size = 0

    print(f"[cleanup] Cleaning up segment files in: {segments_dir}")

    # Walk through directory recursively (handles per-streamer subdirectories)
    for root, dirs, files in os.walk(segments_dir):
        for filename in files:
            # Match common segment file extensions
            if not (filename.endswith('.ts') or filename.endswith('.m4s') or
                    filename.endswith('.tmp') or filename.startswith('chunk_')):
                continue

            filepath = os.path.join(root, filename)

            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                deleted_count += 1
                total_size += file_size

            except OSError as e:
                print(f"[cleanup] Error deleting {filepath}: {e}")
            except Exception as e:
                print(f"[cleanup] Unexpected error for {filepath}: {e}")

    if deleted_count > 0:
        total_size_mb = total_size / (1024 * 1024)
        print(f"[cleanup] Deleted {deleted_count} segment file(s) ({total_size_mb:.1f} MB)")
    else:
        print("[cleanup] No segment files to clean up")

    return deleted_count


def get_clips_summary(clips_dir: str = CLIPS_DIR) -> dict:
    """
    Get a summary of clips in the directory.

    Returns:
        Dictionary with count, total_size_mb, oldest_age_days
    """
    if not os.path.exists(clips_dir):
        return {"count": 0, "total_size_mb": 0, "oldest_age_days": 0}

    count = 0
    total_size = 0
    oldest_mtime = None

    for root, dirs, files in os.walk(clips_dir):
        for filename in files:
            if not filename.lower().endswith('.mp4'):
                continue

            filepath = os.path.join(root, filename)

            try:
                file_size = os.path.getsize(filepath)
                file_mtime = os.path.getmtime(filepath)

                count += 1
                total_size += file_size

                if oldest_mtime is None or file_mtime < oldest_mtime:
                    oldest_mtime = file_mtime

            except OSError:
                pass

    oldest_age_days = 0
    if oldest_mtime:
        oldest_age_days = (datetime.now().timestamp() - oldest_mtime) / 86400

    return {
        "count": count,
        "total_size_mb": total_size / (1024 * 1024),
        "oldest_age_days": oldest_age_days
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup utility for clips and segments"
    )
    parser.add_argument(
        "--clips", "-c",
        action="store_true",
        help="Clean up old clip files"
    )
    parser.add_argument(
        "--segments", "-s",
        action="store_true",
        help="Clean up all segment files"
    )
    parser.add_argument(
        "--days", "-d",
        type=int,
        default=7,
        help="Maximum age in days for clips (default: 7)"
    )
    parser.add_argument(
        "--clips-dir",
        type=str,
        default=CLIPS_DIR,
        help=f"Clips directory path (default: {CLIPS_DIR})"
    )
    parser.add_argument(
        "--segments-dir",
        type=str,
        default=SEGMENTS_DIR,
        help=f"Segments directory path (default: {SEGMENTS_DIR})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary of clips without deleting"
    )

    args = parser.parse_args()

    # Show summary if requested
    if args.summary:
        summary = get_clips_summary(args.clips_dir)
        print(f"\n{'='*50}")
        print("  CLIPS SUMMARY")
        print(f"{'='*50}")
        print(f"  Total clips: {summary['count']}")
        print(f"  Total size: {summary['total_size_mb']:.1f} MB")
        print(f"  Oldest clip: {summary['oldest_age_days']:.1f} days")
        print(f"{'='*50}\n")
        return

    # If neither --clips nor --segments specified, show help
    if not args.clips and not args.segments:
        parser.print_help()
        print("\nExample usage:")
        print("  python src/utils/cleanup.py --clips --days 7")
        print("  python src/utils/cleanup.py --segments")
        print("  python src/utils/cleanup.py --clips --segments --days 14")
        return

    total_deleted = 0

    # Clean up segments
    if args.segments:
        if args.dry_run:
            print("[dry-run] Would clean up segment files")
        else:
            count = cleanup_old_segments(args.segments_dir)
            total_deleted += count

    # Clean up old clips
    if args.clips:
        if args.dry_run:
            print(f"[dry-run] Would delete clips older than {args.days} days")
        else:
            count = cleanup_old_clips(args.clips_dir, args.days)
            total_deleted += count

    print(f"\n[cleanup] Total files deleted: {total_deleted}")


if __name__ == "__main__":
    main()
