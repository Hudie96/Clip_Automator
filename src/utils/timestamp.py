"""
Timestamp conversion utilities for stream clipping.
"""

from datetime import datetime, timedelta


def seconds_to_ffmpeg_time(seconds: float) -> str:
    """
    Convert seconds to FFmpeg timestamp format (HH:MM:SS.mmm).

    Examples:
        90.5 -> "00:01:30.500"
        3661.25 -> "01:01:01.250"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def ffmpeg_time_to_seconds(timestamp: str) -> float:
    """
    Convert FFmpeg timestamp (HH:MM:SS or HH:MM:SS.mmm) to seconds.

    Examples:
        "00:01:30" -> 90.0
        "01:01:01.250" -> 3661.25
    """
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: float) -> str:
    """
    Format duration for human-readable display.

    Examples:
        90 -> "1m 30s"
        3661 -> "1h 1m 1s"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def get_clip_window(
    moment_seconds: float,
    before: int = 30,
    after: int = 30,
    max_duration: float = None
) -> tuple:
    """
    Calculate the start and end times for a clip window.

    Args:
        moment_seconds: The moment to clip around (in seconds)
        before: Seconds to include before the moment
        after: Seconds to include after the moment
        max_duration: Maximum video duration (to prevent going past end)

    Returns:
        (start_seconds, duration_seconds)
    """
    start = max(0, moment_seconds - before)
    end = moment_seconds + after

    if max_duration and end > max_duration:
        end = max_duration

    duration = end - start
    return (start, duration)


def generate_clip_filename(
    streamer: str,
    moment_seconds: float,
    moment_id: int = None
) -> str:
    """
    Generate a filename for a clip.

    Example: "clavicular_moment_01h23m45s_001.mp4"
    """
    time_str = format_duration(moment_seconds).replace(" ", "")
    timestamp = datetime.now().strftime("%Y%m%d")

    if moment_id:
        return f"{streamer}_moment_{time_str}_{moment_id:03d}_{timestamp}.mp4"
    else:
        return f"{streamer}_moment_{time_str}_{timestamp}.mp4"


def parse_stream_start_time(api_response: dict) -> datetime:
    """
    Parse the stream start time from Kick API response.

    The API returns ISO format: "2024-01-15T10:30:00.000000Z"
    """
    livestream = api_response.get('livestream', {})
    start_time_str = livestream.get('created_at') or livestream.get('start_time')

    if not start_time_str:
        return None

    # Handle various ISO format variations
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(start_time_str, fmt)
        except ValueError:
            continue

    return None


def calculate_stream_elapsed(stream_start: datetime) -> float:
    """
    Calculate how many seconds have elapsed since stream started.
    """
    if not stream_start:
        return 0.0

    elapsed = datetime.utcnow() - stream_start
    return elapsed.total_seconds()


if __name__ == "__main__":
    # Quick tests
    print("Testing timestamp utilities:")
    print(f"  90.5 seconds -> {seconds_to_ffmpeg_time(90.5)}")
    print(f"  '00:01:30.500' -> {ffmpeg_time_to_seconds('00:01:30.500')} seconds")
    print(f"  3661 seconds -> {format_duration(3661)}")
    print(f"  Clip window at 120s: {get_clip_window(120, 30, 30)}")
    print(f"  Filename: {generate_clip_filename('clavicular', 3661, 1)}")
