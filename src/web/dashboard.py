"""
Flask-based web dashboard for monitoring clips and streams.
Run with: python src/web/dashboard.py --port 5000
"""

import argparse
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, send_file, abort
from flask_socketio import SocketIO, emit

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.web.api import api_bp
from src.web.live_stats import shared_stats

# Get project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLIPS_DIR = PROJECT_ROOT / "clips"
STREAMERS_JSON = PROJECT_ROOT / "config" / "streamers.json"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*")

# Register API blueprint
app.register_blueprint(api_bp)


def get_streamers():
    """Load configured streamers from config file."""
    try:
        with open(STREAMERS_JSON, 'r') as f:
            data = json.load(f)
            return data.get('streamers', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_clip_metadata(clip_path: Path) -> dict:
    """Get metadata for a clip file."""
    stat = clip_path.stat()

    # Parse filename for details
    # Format: streamer_trigger_YYYYMMDD_HHMMSS_NNN.mp4
    filename = clip_path.name
    parts = filename.replace('.mp4', '').split('_')

    streamer = parts[0] if len(parts) > 0 else "unknown"
    trigger = parts[1] if len(parts) > 1 else "unknown"

    # Try to parse date/time from filename
    try:
        if len(parts) >= 4:
            date_str = parts[2]
            time_str = parts[3]
            clip_datetime = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        else:
            clip_datetime = datetime.fromtimestamp(stat.st_mtime)
    except (ValueError, IndexError):
        clip_datetime = datetime.fromtimestamp(stat.st_mtime)

    # Check for thumbnail
    thumbnail_name = clip_path.stem + ".jpg"
    thumbnail_path = clip_path.parent / thumbnail_name
    has_thumbnail = thumbnail_path.exists()

    return {
        'filename': filename,
        'path': str(clip_path.relative_to(CLIPS_DIR)),
        'streamer': streamer,
        'trigger': trigger,
        'datetime': clip_datetime.isoformat(),
        'datetime_display': clip_datetime.strftime("%Y-%m-%d %H:%M:%S"),
        'size_bytes': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'has_thumbnail': has_thumbnail,
        'thumbnail': thumbnail_name if has_thumbnail else None
    }


def get_all_clips():
    """Get all clips from clips directory and subdirectories."""
    clips = []

    if not CLIPS_DIR.exists():
        return clips

    # Get clips from root clips dir
    for clip_file in CLIPS_DIR.glob("*.mp4"):
        clips.append(get_clip_metadata(clip_file))

    # Get clips from streamer subdirectories
    for subdir in CLIPS_DIR.iterdir():
        if subdir.is_dir():
            for clip_file in subdir.glob("*.mp4"):
                clips.append(get_clip_metadata(clip_file))

    # Sort by datetime, newest first
    clips.sort(key=lambda x: x['datetime'], reverse=True)

    return clips


def get_stats():
    """Calculate basic stats for the dashboard."""
    clips = get_all_clips()
    total_clips = len(clips)
    total_size_bytes = sum(c['size_bytes'] for c in clips)
    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
    total_size_gb = round(total_size_bytes / (1024 * 1024 * 1024), 2)

    # Count by trigger type
    triggers = {}
    for clip in clips:
        trigger = clip['trigger']
        triggers[trigger] = triggers.get(trigger, 0) + 1

    # Count by streamer
    streamers = {}
    for clip in clips:
        streamer = clip['streamer']
        streamers[streamer] = streamers.get(streamer, 0) + 1

    return {
        'total_clips': total_clips,
        'total_size_mb': total_size_mb,
        'total_size_gb': total_size_gb,
        'triggers': triggers,
        'streamers': streamers
    }


def generate_thumbnail(clip_path: Path) -> Path:
    """Generate a thumbnail for a clip using FFmpeg."""
    thumbnail_path = clip_path.with_suffix('.jpg')

    if thumbnail_path.exists():
        return thumbnail_path

    try:
        # Extract frame at 1 second mark
        subprocess.run([
            'ffmpeg', '-y', '-i', str(clip_path),
            '-ss', '00:00:01',
            '-vframes', '1',
            '-vf', 'scale=320:-1',
            str(thumbnail_path)
        ], capture_output=True, timeout=30)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return thumbnail_path if thumbnail_path.exists() else None


@app.route('/')
def dashboard():
    """Dashboard home page."""
    clips = get_all_clips()[:50]  # Show last 50 clips
    streamers = get_streamers()
    stats = get_stats()

    return render_template('dashboard.html',
                         clips=clips,
                         streamers=streamers,
                         stats=stats)


@app.route('/clips')
def clips_api():
    """JSON API returning list of clips with metadata."""
    clips = get_all_clips()
    return jsonify({
        'clips': clips,
        'stats': get_stats()
    })


@app.route('/api/stats')
def live_stats_api():
    """JSON API returning real-time statistics."""
    return jsonify(shared_stats.get_all_stats())


@app.route('/api/stream-url/<streamer>')
def stream_url_api(streamer):
    """Return the stream embed URL for a streamer."""
    # For Kick, we use the player embed URL
    return jsonify({
        'streamer': streamer,
        'embed_url': f'https://player.kick.com/{streamer}',
        'chat_url': f'https://kick.com/{streamer}/chatroom'
    })


@app.route('/clips/<path:filename>')
def serve_clip(filename):
    """Serve the actual clip file."""
    # Try root clips directory first
    clip_path = CLIPS_DIR / filename

    if not clip_path.exists():
        # Try in subdirectories
        for subdir in CLIPS_DIR.iterdir():
            if subdir.is_dir():
                potential_path = subdir / filename
                if potential_path.exists():
                    clip_path = potential_path
                    break

    if not clip_path.exists():
        abort(404)

    # Security: ensure path is within CLIPS_DIR
    try:
        clip_path.resolve().relative_to(CLIPS_DIR.resolve())
    except ValueError:
        abort(403)

    return send_file(clip_path, mimetype='video/mp4')


@app.route('/thumbnails/<path:filename>')
def serve_thumbnail(filename):
    """Serve thumbnail images."""
    # Convert to jpg if not already
    if not filename.endswith('.jpg'):
        filename = Path(filename).stem + '.jpg'

    # Try root clips directory first
    thumb_path = CLIPS_DIR / filename

    if not thumb_path.exists():
        # Try in subdirectories
        for subdir in CLIPS_DIR.iterdir():
            if subdir.is_dir():
                potential_path = subdir / filename
                if potential_path.exists():
                    thumb_path = potential_path
                    break

    if not thumb_path.exists():
        # Try to generate from video
        video_filename = Path(filename).stem + '.mp4'
        video_path = CLIPS_DIR / video_filename

        if not video_path.exists():
            for subdir in CLIPS_DIR.iterdir():
                if subdir.is_dir():
                    potential_path = subdir / video_filename
                    if potential_path.exists():
                        video_path = potential_path
                        break

        if video_path.exists():
            generated = generate_thumbnail(video_path)
            if generated:
                thumb_path = generated

    if not thumb_path.exists():
        abort(404)

    # Security: ensure path is within CLIPS_DIR
    try:
        thumb_path.resolve().relative_to(CLIPS_DIR.resolve())
    except ValueError:
        abort(403)

    return send_file(thumb_path, mimetype='image/jpeg')


# WebSocket event handlers
@socketio.on('request_stats')
def handle_stats_request():
    """Handle client request for current stats via WebSocket."""
    emit('stats_update', shared_stats.get_all_stats())


def emit_stats_update():
    """
    Broadcast current stats to all connected WebSocket clients.
    Call this function from the clipper to push updates in real-time.
    """
    socketio.emit('stats_update', shared_stats.get_all_stats())


def main():
    """Run the dashboard server."""
    parser = argparse.ArgumentParser(description='Clip Automater Dashboard')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"Starting Clip Automater Dashboard on http://{args.host}:{args.port}")
    print(f"Clips directory: {CLIPS_DIR}")
    print(f"Streamers config: {STREAMERS_JSON}")
    print(f"WebSocket support: enabled")

    socketio.run(app, host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
