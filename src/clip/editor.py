"""
Clip editor - provides trimming functionality using FFmpeg.

This module handles:
1. Trimming clips by setting start/end points
2. Getting video metadata (duration, etc.)
3. Progress reporting during export
"""

import subprocess
import os
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Tuple


def get_video_duration(video_path: str) -> Optional[float]:
    """
    Get the duration of a video file in seconds using FFprobe.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds, or None if unable to determine
    """
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


def get_video_metadata(video_path: str) -> dict:
    """
    Get comprehensive metadata for a video file.

    Args:
        video_path: Path to the video file

    Returns:
        Dictionary containing video metadata
    """
    metadata = {
        'duration': None,
        'width': None,
        'height': None,
        'fps': None,
        'codec': None,
        'size_bytes': None
    }

    # Get file size
    if os.path.exists(video_path):
        metadata['size_bytes'] = os.path.getsize(video_path)

    # Get duration
    metadata['duration'] = get_video_duration(video_path)

    # Get video stream info
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,r_frame_rate,codec_name',
        '-of', 'csv=p=0',
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(',')
        if len(parts) >= 4:
            metadata['width'] = int(parts[0]) if parts[0] else None
            metadata['height'] = int(parts[1]) if parts[1] else None
            # Parse frame rate (e.g., "30/1" or "30000/1001")
            if '/' in parts[2]:
                num, den = parts[2].split('/')
                metadata['fps'] = round(float(num) / float(den), 2) if float(den) != 0 else None
            metadata['codec'] = parts[3] if parts[3] else None
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass

    return metadata


def parse_time_input(time_input) -> float:
    """
    Parse various time input formats into seconds.

    Accepts:
        - Float or int (seconds): 90.5
        - String with seconds: "90.5"
        - String with MM:SS: "01:30"
        - String with HH:MM:SS: "00:01:30"
        - String with HH:MM:SS.mmm: "00:01:30.500"

    Args:
        time_input: Time in various formats

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If format is invalid
    """
    if isinstance(time_input, (int, float)):
        return float(time_input)

    if not isinstance(time_input, str):
        raise ValueError(f"Invalid time format: {time_input}")

    time_str = time_input.strip()

    # Try parsing as pure number first
    try:
        return float(time_str)
    except ValueError:
        pass

    # Parse timestamp format
    parts = time_str.split(':')

    try:
        if len(parts) == 2:
            # MM:SS format
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 3:
            # HH:MM:SS format
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            raise ValueError(f"Invalid time format: {time_input}")
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid time format: {time_input}") from e


def seconds_to_timecode(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format for FFmpeg.

    Args:
        seconds: Time in seconds

    Returns:
        Timecode string in HH:MM:SS.mmm format
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def generate_output_filename(
    original_path: str,
    suffix: str = "trimmed",
    output_dir: Optional[str] = None
) -> str:
    """
    Generate a unique output filename for the trimmed clip.

    Args:
        original_path: Path to the original video file
        suffix: Suffix to add before extension (default: "trimmed")
        output_dir: Optional output directory (defaults to same as original)

    Returns:
        Path to the output file
    """
    original = Path(original_path)
    stem = original.stem
    ext = original.suffix

    # Generate timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create new filename
    new_filename = f"{stem}_{suffix}_{timestamp}{ext}"

    # Determine output directory
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = original.parent

    return str(out_dir / new_filename)


def trim_clip(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Tuple[bool, str]:
    """
    Trim a video clip using FFmpeg with stream copy (no re-encoding).

    Uses FFmpeg's -ss (before -i for fast seek) and -to flags
    with -c copy for fast, lossless trimming.

    Args:
        input_path: Path to the source video file
        output_path: Path for the output trimmed clip
        start_time: Start time in seconds
        end_time: End time in seconds
        progress_callback: Optional callback(message, progress_percent)

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate inputs
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"

    if start_time < 0:
        return False, "Start time cannot be negative"

    if end_time <= start_time:
        return False, "End time must be greater than start time"

    # Get video duration to validate
    duration = get_video_duration(input_path)
    if duration and end_time > duration:
        return False, f"End time ({end_time}s) exceeds video duration ({duration}s)"

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert times to FFmpeg format
    start_timecode = seconds_to_timecode(start_time)
    end_timecode = seconds_to_timecode(end_time)

    if progress_callback:
        progress_callback("Preparing trim operation...", 10)

    # Build FFmpeg command
    # Using -ss before -i for fast seeking (input seeking)
    # Using -to for end time (relative to start of output)
    # Using -c copy for stream copy (no re-encoding)
    cmd = [
        'ffmpeg',
        '-y',                          # Overwrite output file
        '-ss', start_timecode,         # Start time (before -i for fast seek)
        '-i', input_path,              # Input file
        '-to', seconds_to_timecode(end_time - start_time),  # Duration relative to output
        '-c', 'copy',                  # Copy streams without re-encoding
        '-avoid_negative_ts', 'make_zero',  # Handle timestamp issues
        '-map', '0',                   # Map all streams
        output_path
    ]

    if progress_callback:
        progress_callback("Trimming clip...", 30)

    try:
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit
        )

        if progress_callback:
            progress_callback("Verifying output...", 80)

        # Check if output was created
        if not os.path.exists(output_path):
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            return False, f"FFmpeg failed to create output: {error_msg}"

        # Verify output file has content
        output_size = os.path.getsize(output_path)
        if output_size < 1000:  # Less than 1KB is probably an error
            return False, "Output file is too small, trim may have failed"

        if progress_callback:
            progress_callback("Trim complete!", 100)

        # Calculate trimmed duration
        trimmed_duration = end_time - start_time

        return True, f"Successfully trimmed clip ({trimmed_duration:.1f}s)"

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr[:500] if e.stderr else str(e)
        return False, f"FFmpeg error: {error_msg}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def trim_clip_with_reencode(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Tuple[bool, str]:
    """
    Trim a video clip using FFmpeg with re-encoding for precise cuts.

    This is slower but provides frame-accurate trimming.
    Use this when stream copy results in imprecise cuts.

    Args:
        input_path: Path to the source video file
        output_path: Path for the output trimmed clip
        start_time: Start time in seconds
        end_time: End time in seconds
        progress_callback: Optional callback(message, progress_percent)

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Validate inputs
    if not os.path.exists(input_path):
        return False, f"Input file not found: {input_path}"

    if start_time < 0:
        return False, "Start time cannot be negative"

    if end_time <= start_time:
        return False, "End time must be greater than start time"

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert times to FFmpeg format
    start_timecode = seconds_to_timecode(start_time)
    duration = end_time - start_time

    if progress_callback:
        progress_callback("Preparing trim with re-encode...", 10)

    # Build FFmpeg command with re-encoding
    cmd = [
        'ffmpeg',
        '-y',                          # Overwrite output file
        '-ss', start_timecode,         # Start time
        '-i', input_path,              # Input file
        '-t', str(duration),           # Duration
        '-c:v', 'libx264',             # Video codec
        '-preset', 'fast',             # Encoding speed preset
        '-crf', '18',                  # Quality (lower = better)
        '-c:a', 'aac',                 # Audio codec
        '-b:a', '192k',                # Audio bitrate
        '-avoid_negative_ts', 'make_zero',
        output_path
    ]

    if progress_callback:
        progress_callback("Re-encoding clip (this may take a moment)...", 30)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if progress_callback:
            progress_callback("Verifying output...", 90)

        if not os.path.exists(output_path):
            error_msg = result.stderr[:500] if result.stderr else "Unknown error"
            return False, f"FFmpeg failed to create output: {error_msg}"

        output_size = os.path.getsize(output_path)
        if output_size < 1000:
            return False, "Output file is too small, trim may have failed"

        if progress_callback:
            progress_callback("Trim complete!", 100)

        return True, f"Successfully trimmed and re-encoded clip ({duration:.1f}s)"

    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


# Convenience function for API use
def trim_clip_api(
    input_path: str,
    start_time,
    end_time,
    output_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    reencode: bool = False,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> dict:
    """
    API-friendly wrapper for clip trimming.

    Args:
        input_path: Path to the source video
        start_time: Start time (seconds or timestamp string)
        end_time: End time (seconds or timestamp string)
        output_name: Optional custom output filename
        output_dir: Optional output directory
        reencode: Whether to re-encode (slower but more precise)
        progress_callback: Optional callback for progress updates

    Returns:
        Dictionary with result information
    """
    try:
        # Parse time inputs
        start_seconds = parse_time_input(start_time)
        end_seconds = parse_time_input(end_time)
    except ValueError as e:
        return {
            'success': False,
            'error': str(e),
            'output_path': None,
            'duration': None
        }

    # Generate output path
    if output_name:
        # Use provided name
        original = Path(input_path)
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = original.parent

        # Ensure extension
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'

        output_path = str(out_dir / output_name)
    else:
        output_path = generate_output_filename(input_path, "trimmed", output_dir)

    # Perform trim
    if reencode:
        success, message = trim_clip_with_reencode(
            input_path, output_path, start_seconds, end_seconds, progress_callback
        )
    else:
        success, message = trim_clip(
            input_path, output_path, start_seconds, end_seconds, progress_callback
        )

    # Build response
    result = {
        'success': success,
        'message': message,
        'output_path': output_path if success else None,
        'duration': end_seconds - start_seconds if success else None
    }

    if success:
        result['output_filename'] = Path(output_path).name
        result['output_size_bytes'] = os.path.getsize(output_path)
    else:
        result['error'] = message

    return result


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) < 4:
        print("Usage: python editor.py <input_path> <start_time> <end_time>")
        print("  Times can be in seconds (90.5) or timestamp format (01:30:00)")
        sys.exit(1)

    input_path = sys.argv[1]
    start_time = sys.argv[2]
    end_time = sys.argv[3]

    def print_progress(msg, pct):
        print(f"  [{pct:3d}%] {msg}")

    print(f"Trimming: {input_path}")
    print(f"  From: {start_time}")
    print(f"  To: {end_time}")

    result = trim_clip_api(
        input_path,
        start_time,
        end_time,
        progress_callback=print_progress
    )

    if result['success']:
        print(f"\nSuccess! Output: {result['output_path']}")
        print(f"Duration: {result['duration']:.1f}s")
        print(f"Size: {result['output_size_bytes'] / 1024 / 1024:.2f} MB")
    else:
        print(f"\nFailed: {result['error']}")
