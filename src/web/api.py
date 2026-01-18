"""
REST API endpoints for clip management.
Handles clip deletion, renaming, favorite management, review workflow, streamer management, and VOD clipping.
"""

import json
import os
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.db.schema import (
    get_pending_clips, get_clip_by_id, approve_clip, reject_clip,
    delete_clip_record, get_clip_stats, register_clip
)
from src.web.streamer_search import search_streamers, get_channel_info, check_streamer_live
from src.vod.vod_clipper import VODClipper
from src.vod.chat_analyzer import ChatAnalyzer

# VOD clipping instances (singleton-like)
_vod_clipper = None
_chat_analyzer = None
_vod_clip_jobs = {}  # Track in-progress clipping jobs

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLIPS_DIR = PROJECT_ROOT / "clips"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
FAVORITES_FILE = DATA_DIR / "favorites.json"
STREAMERS_FILE = CONFIG_DIR / "streamers.json"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

api_bp = Blueprint('api', __name__, url_prefix='/api')


def load_favorites():
    """Load favorites list from JSON file."""
    if FAVORITES_FILE.exists():
        try:
            with open(FAVORITES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_favorites(favorites):
    """Save favorites list to JSON file."""
    try:
        with open(FAVORITES_FILE, 'w') as f:
            json.dump(favorites, f, indent=2)
        return True
    except IOError:
        return False


def find_clip_path(filename):
    """
    Find a clip file in CLIPS_DIR or its subdirectories.
    Returns the full path if found, None otherwise.
    """
    # Try root clips directory first
    clip_path = CLIPS_DIR / filename

    if clip_path.exists():
        return clip_path

    # Try in subdirectories
    if CLIPS_DIR.exists():
        for subdir in CLIPS_DIR.iterdir():
            if subdir.is_dir():
                potential_path = subdir / filename
                if potential_path.exists():
                    return potential_path

    return None


def find_thumbnail_path(filename):
    """
    Find a thumbnail file (by stem) in CLIPS_DIR or its subdirectories.
    Returns the full path if found, None otherwise.
    """
    # Convert to jpg if not already
    stem = Path(filename).stem
    thumbnail_name = f"{stem}.jpg"

    # Try root clips directory first
    thumb_path = CLIPS_DIR / thumbnail_name

    if thumb_path.exists():
        return thumb_path

    # Try in subdirectories
    if CLIPS_DIR.exists():
        for subdir in CLIPS_DIR.iterdir():
            if subdir.is_dir():
                potential_path = subdir / thumbnail_name
                if potential_path.exists():
                    return potential_path

    return None


@api_bp.route('/clips/<filename>', methods=['DELETE'])
def delete_clip(filename):
    """Delete a clip file and its thumbnail."""
    clip_path = find_clip_path(filename)

    if not clip_path:
        return jsonify({
            'success': False,
            'error': 'Clip not found',
            'code': 'NOT_FOUND'
        }), 404

    try:
        # Delete the clip file
        clip_path.unlink()

        # Delete the thumbnail if it exists
        thumbnail_path = find_thumbnail_path(filename)
        if thumbnail_path:
            thumbnail_path.unlink()

        # Remove from favorites if present
        favorites = load_favorites()
        if filename in favorites:
            favorites.remove(filename)
            save_favorites(favorites)

        return jsonify({
            'success': True,
            'message': 'Clip deleted successfully',
            'filename': filename
        }), 200

    except OSError as e:
        return jsonify({
            'success': False,
            'error': f'Failed to delete clip: {str(e)}',
            'code': 'DELETE_ERROR'
        }), 500


@api_bp.route('/clips/<filename>', methods=['PATCH'])
def rename_clip(filename):
    """Rename a clip file."""
    data = request.get_json()

    if not data or 'new_name' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: new_name',
            'code': 'INVALID_REQUEST'
        }), 400

    new_name = data['new_name'].strip()

    if not new_name:
        return jsonify({
            'success': False,
            'error': 'new_name cannot be empty',
            'code': 'INVALID_REQUEST'
        }), 400

    # Ensure new name has .mp4 extension
    if not new_name.endswith('.mp4'):
        new_name += '.mp4'

    clip_path = find_clip_path(filename)

    if not clip_path:
        return jsonify({
            'success': False,
            'error': 'Clip not found',
            'code': 'NOT_FOUND'
        }), 404

    # Check if new name already exists
    new_path = clip_path.parent / new_name
    if new_path.exists():
        return jsonify({
            'success': False,
            'error': 'A clip with that name already exists',
            'code': 'CONFLICT'
        }), 409

    try:
        # Rename the clip file
        clip_path.rename(new_path)

        # Rename thumbnail if it exists
        thumbnail_path = find_thumbnail_path(filename)
        if thumbnail_path:
            new_stem = Path(new_name).stem
            new_thumbnail_name = f"{new_stem}.jpg"
            new_thumbnail_path = thumbnail_path.parent / new_thumbnail_name
            thumbnail_path.rename(new_thumbnail_path)

        # Update favorites if the old filename was favorited
        favorites = load_favorites()
        if filename in favorites:
            favorites.remove(filename)
            favorites.append(new_name)
            save_favorites(favorites)

        return jsonify({
            'success': True,
            'message': 'Clip renamed successfully',
            'old_filename': filename,
            'new_filename': new_name
        }), 200

    except (OSError, ValueError) as e:
        return jsonify({
            'success': False,
            'error': f'Failed to rename clip: {str(e)}',
            'code': 'RENAME_ERROR'
        }), 500


@api_bp.route('/clips/<filename>/favorite', methods=['POST'])
def toggle_favorite(filename):
    """Toggle favorite status for a clip."""
    clip_path = find_clip_path(filename)

    if not clip_path:
        return jsonify({
            'success': False,
            'error': 'Clip not found',
            'code': 'NOT_FOUND'
        }), 404

    try:
        favorites = load_favorites()
        is_favorited = filename in favorites

        if is_favorited:
            favorites.remove(filename)
        else:
            favorites.append(filename)

        if not save_favorites(favorites):
            raise IOError("Failed to save favorites")

        return jsonify({
            'success': True,
            'message': f'Clip {"removed from" if is_favorited else "added to"} favorites',
            'filename': filename,
            'is_favorited': not is_favorited
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to update favorite status: {str(e)}',
            'code': 'FAVORITE_ERROR'
        }), 500


@api_bp.route('/favorites', methods=['GET'])
def get_favorites():
    """Get list of favorited clips."""
    try:
        favorites = load_favorites()

        # Enrich with metadata for favorited clips
        favorited_clips = []
        for filename in favorites:
            clip_path = find_clip_path(filename)
            if clip_path and clip_path.exists():
                stat = clip_path.stat()
                favorited_clips.append({
                    'filename': filename,
                    'exists': True,
                    'size_bytes': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2)
                })
            else:
                # File no longer exists, mark it
                favorited_clips.append({
                    'filename': filename,
                    'exists': False
                })

        return jsonify({
            'success': True,
            'favorites': favorited_clips,
            'total': len(favorited_clips)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to retrieve favorites: {str(e)}',
            'code': 'FETCH_ERROR'
        }), 500


# ==================
# Clip Review API
# ==================

@api_bp.route('/review/pending', methods=['GET'])
def get_pending_review():
    """Get clips pending review."""
    streamer = request.args.get('streamer')
    limit = request.args.get('limit', 50, type=int)

    try:
        clips = get_pending_clips(streamer=streamer, limit=limit)

        # Enrich with file info
        for clip in clips:
            clip_path = find_clip_path(Path(clip['clip_path']).name)
            if clip_path and clip_path.exists():
                clip['exists'] = True
                clip['size_mb'] = round(clip_path.stat().st_size / (1024 * 1024), 2)
                clip['filename'] = clip_path.name
                clip['url'] = f"/clips/{clip_path.name}"
                clip['thumbnail_url'] = f"/thumbnails/{clip_path.stem}.jpg"
            else:
                clip['exists'] = False

        return jsonify({
            'success': True,
            'clips': clips,
            'total': len(clips)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'FETCH_ERROR'
        }), 500


@api_bp.route('/review/stats', methods=['GET'])
def get_review_stats():
    """Get review statistics."""
    try:
        stats = get_clip_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'FETCH_ERROR'
        }), 500


@api_bp.route('/review/<int:clip_id>/approve', methods=['POST'])
def approve_clip_endpoint(clip_id):
    """Approve a clip."""
    data = request.get_json() or {}
    notes = data.get('notes')

    try:
        clip = get_clip_by_id(clip_id)
        if not clip:
            return jsonify({
                'success': False,
                'error': 'Clip not found',
                'code': 'NOT_FOUND'
            }), 404

        success = approve_clip(clip_id, notes)

        return jsonify({
            'success': success,
            'message': 'Clip approved' if success else 'Failed to approve clip',
            'clip_id': clip_id
        }), 200 if success else 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'APPROVE_ERROR'
        }), 500


@api_bp.route('/review/<int:clip_id>/reject', methods=['POST'])
def reject_clip_endpoint(clip_id):
    """Reject a clip (marks for deletion)."""
    data = request.get_json() or {}
    notes = data.get('notes')

    try:
        clip = get_clip_by_id(clip_id)
        if not clip:
            return jsonify({
                'success': False,
                'error': 'Clip not found',
                'code': 'NOT_FOUND'
            }), 404

        success = reject_clip(clip_id, notes)

        return jsonify({
            'success': success,
            'message': 'Clip rejected' if success else 'Failed to reject clip',
            'clip_id': clip_id
        }), 200 if success else 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'REJECT_ERROR'
        }), 500


@api_bp.route('/review/<int:clip_id>', methods=['DELETE'])
def delete_clip_review(clip_id):
    """Delete a clip immediately (both file and database record)."""
    try:
        clip = get_clip_by_id(clip_id)
        if not clip:
            return jsonify({
                'success': False,
                'error': 'Clip not found',
                'code': 'NOT_FOUND'
            }), 404

        # Delete the actual file
        clip_path = find_clip_path(Path(clip['clip_path']).name)
        if clip_path and clip_path.exists():
            clip_path.unlink()

            # Delete thumbnail if exists
            thumb_path = find_thumbnail_path(clip_path.name)
            if thumb_path:
                thumb_path.unlink()

        # Delete database record
        delete_clip_record(clip_id)

        return jsonify({
            'success': True,
            'message': 'Clip deleted',
            'clip_id': clip_id
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'DELETE_ERROR'
        }), 500


@api_bp.route('/review/bulk', methods=['POST'])
def bulk_review():
    """Bulk approve or reject clips."""
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'Missing request body',
            'code': 'INVALID_REQUEST'
        }), 400

    action = data.get('action')  # 'approve' or 'reject'
    clip_ids = data.get('clip_ids', [])

    if action not in ['approve', 'reject']:
        return jsonify({
            'success': False,
            'error': 'Invalid action. Must be "approve" or "reject"',
            'code': 'INVALID_REQUEST'
        }), 400

    if not clip_ids:
        return jsonify({
            'success': False,
            'error': 'No clip IDs provided',
            'code': 'INVALID_REQUEST'
        }), 400

    try:
        results = {'success': 0, 'failed': 0}

        for clip_id in clip_ids:
            if action == 'approve':
                if approve_clip(clip_id):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            else:  # reject
                if reject_clip(clip_id):
                    results['success'] += 1
                else:
                    results['failed'] += 1

        return jsonify({
            'success': True,
            'message': f'{action.capitalize()}d {results["success"]} clips',
            'results': results
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'BULK_ERROR'
        }), 500


# ==================
# Streamer Management API
# ==================

def load_streamers():
    """Load streamers list from JSON file."""
    if STREAMERS_FILE.exists():
        try:
            with open(STREAMERS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('streamers', [])
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_streamers(streamers):
    """Save streamers list to JSON file."""
    try:
        # Ensure config directory exists
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(STREAMERS_FILE, 'w') as f:
            json.dump({'streamers': streamers}, f, indent=2)
        return True
    except IOError:
        return False


@api_bp.route('/streamers/search', methods=['GET'])
def search_streamers_endpoint():
    """Search for streamers on Kick."""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required',
            'code': 'INVALID_REQUEST'
        }), 400

    if len(query) < 1:
        return jsonify({
            'success': False,
            'error': 'Search query must be at least 1 character',
            'code': 'INVALID_REQUEST'
        }), 400

    try:
        results = search_streamers(query, limit=min(limit, 25))

        # Mark which streamers are already being monitored
        monitored = set(load_streamers())
        for result in results:
            result['is_monitored'] = result['username'].lower() in [s.lower() for s in monitored]

        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'total': len(results)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}',
            'code': 'SEARCH_ERROR'
        }), 500


@api_bp.route('/streamers/add', methods=['POST'])
def add_streamer():
    """Add a streamer to the monitoring list."""
    data = request.get_json()

    if not data or 'username' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required field: username',
            'code': 'INVALID_REQUEST'
        }), 400

    username = data['username'].strip().lower()

    if not username:
        return jsonify({
            'success': False,
            'error': 'Username cannot be empty',
            'code': 'INVALID_REQUEST'
        }), 400

    try:
        streamers = load_streamers()

        # Check if already monitoring
        if username in [s.lower() for s in streamers]:
            return jsonify({
                'success': False,
                'error': 'Streamer is already being monitored',
                'code': 'ALREADY_EXISTS'
            }), 409

        # Verify streamer exists on Kick
        channel_info = get_channel_info(username)
        if not channel_info:
            return jsonify({
                'success': False,
                'error': 'Streamer not found on Kick',
                'code': 'NOT_FOUND'
            }), 404

        # Add to list
        streamers.append(username)

        if not save_streamers(streamers):
            return jsonify({
                'success': False,
                'error': 'Failed to save streamers list',
                'code': 'SAVE_ERROR'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Added {username} to monitoring list',
            'username': username,
            'channel_info': channel_info
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to add streamer: {str(e)}',
            'code': 'ADD_ERROR'
        }), 500


@api_bp.route('/streamers/<username>', methods=['DELETE'])
def remove_streamer(username):
    """Remove a streamer from the monitoring list."""
    username = username.strip().lower()

    try:
        streamers = load_streamers()
        streamers_lower = [s.lower() for s in streamers]

        if username not in streamers_lower:
            return jsonify({
                'success': False,
                'error': 'Streamer is not being monitored',
                'code': 'NOT_FOUND'
            }), 404

        # Find and remove the streamer (case-insensitive)
        for i, s in enumerate(streamers):
            if s.lower() == username:
                streamers.pop(i)
                break

        if not save_streamers(streamers):
            return jsonify({
                'success': False,
                'error': 'Failed to save streamers list',
                'code': 'SAVE_ERROR'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Removed {username} from monitoring list',
            'username': username
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to remove streamer: {str(e)}',
            'code': 'REMOVE_ERROR'
        }), 500


@api_bp.route('/streamers/list', methods=['GET'])
def list_streamers():
    """List all monitored streamers with their live status."""
    try:
        streamers = load_streamers()
        streamer_list = []

        for username in streamers:
            # Get live status for each streamer
            status = check_streamer_live(username)
            streamer_list.append({
                'username': username,
                'is_live': status.get('is_live', False),
                'viewers': status.get('viewers', 0),
                'title': status.get('title', ''),
                'category': status.get('category', '')
            })

        # Sort: live streamers first, then by viewer count
        streamer_list.sort(key=lambda x: (-x['is_live'], -x['viewers']))

        return jsonify({
            'success': True,
            'streamers': streamer_list,
            'total': len(streamer_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to list streamers: {str(e)}',
            'code': 'LIST_ERROR'
        }), 500


@api_bp.route('/streamers/<username>/status', methods=['GET'])
def get_streamer_status(username):
    """Get the current status of a specific streamer."""
    username = username.strip().lower()

    try:
        status = check_streamer_live(username)

        if not status:
            return jsonify({
                'success': False,
                'error': 'Failed to get streamer status',
                'code': 'FETCH_ERROR'
            }), 500

        # Check if streamer is monitored
        streamers = load_streamers()
        status['is_monitored'] = username in [s.lower() for s in streamers]

        return jsonify({
            'success': True,
            'status': status
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}',
            'code': 'STATUS_ERROR'
        }), 500


# ==================
# VOD Clipping API
# ==================

def get_vod_clipper():
    """Get or create the VOD clipper instance."""
    global _vod_clipper
    if _vod_clipper is None:
        _vod_clipper = VODClipper()
    return _vod_clipper


def get_chat_analyzer():
    """Get or create the chat analyzer instance."""
    global _chat_analyzer
    if _chat_analyzer is None:
        _chat_analyzer = ChatAnalyzer()
    return _chat_analyzer


@api_bp.route('/vods/list/<streamer>', methods=['GET'])
def get_vod_list(streamer):
    """
    Get list of VODs for a streamer.

    Query params:
        limit: Maximum number of VODs to return (default: 20, max: 50)
    """
    streamer = streamer.strip().lower()
    limit = request.args.get('limit', 20, type=int)
    limit = min(limit, 50)  # Cap at 50

    try:
        clipper = get_vod_clipper()
        vods = clipper.get_vod_list(streamer, limit=limit)

        return jsonify({
            'success': True,
            'streamer': streamer,
            'vods': [vod.to_dict() for vod in vods],
            'total': len(vods)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch VODs: {str(e)}',
            'code': 'FETCH_ERROR'
        }), 500


@api_bp.route('/vods/details/<vod_id>', methods=['GET'])
def get_vod_details(vod_id):
    """Get detailed information about a specific VOD."""
    try:
        clipper = get_vod_clipper()
        vod = clipper.get_vod_details(vod_id)

        if not vod:
            return jsonify({
                'success': False,
                'error': 'VOD not found',
                'code': 'NOT_FOUND'
            }), 404

        return jsonify({
            'success': True,
            'vod': vod.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to fetch VOD details: {str(e)}',
            'code': 'FETCH_ERROR'
        }), 500


@api_bp.route('/vods/clip', methods=['POST'])
def create_vod_clip():
    """
    Create a clip from a VOD segment (Manual Mode - Free).

    Request body:
        vod_id: The VOD ID to clip from
        start_time: Start timestamp (HH:MM:SS or seconds)
        end_time: End timestamp (HH:MM:SS or seconds)
        streamer: Streamer name (for filename)
        output_name: Optional custom output filename
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'Missing request body',
            'code': 'INVALID_REQUEST'
        }), 400

    # Validate required fields
    required_fields = ['vod_id', 'start_time', 'end_time', 'streamer']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}',
                'code': 'INVALID_REQUEST'
            }), 400

    vod_id = str(data['vod_id'])
    start_time = data['start_time']
    end_time = data['end_time']
    streamer = data['streamer'].strip().lower()
    output_name = data.get('output_name')

    # Generate a job ID for tracking
    import uuid
    job_id = str(uuid.uuid4())[:8]

    try:
        clipper = get_vod_clipper()

        # Validate timestamps
        try:
            start_seconds = clipper.parse_timestamp(start_time)
            end_seconds = clipper.parse_timestamp(end_time)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid timestamp format: {str(e)}',
                'code': 'INVALID_TIMESTAMP'
            }), 400

        if end_seconds <= start_seconds:
            return jsonify({
                'success': False,
                'error': 'End time must be after start time',
                'code': 'INVALID_TIMESTAMP'
            }), 400

        duration = end_seconds - start_seconds
        if duration > 300:  # Max 5 minutes
            return jsonify({
                'success': False,
                'error': 'Clip duration cannot exceed 5 minutes (300 seconds)',
                'code': 'DURATION_EXCEEDED'
            }), 400

        # Start clipping in background thread
        _vod_clip_jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Starting clip creation...',
            'clip_path': None
        }

        def progress_callback(message, progress):
            _vod_clip_jobs[job_id]['message'] = message
            _vod_clip_jobs[job_id]['progress'] = progress

        def clip_worker():
            try:
                clip_path = clipper.create_clip(
                    vod_id=vod_id,
                    start_time=start_time,
                    end_time=end_time,
                    streamer=streamer,
                    output_name=output_name,
                    progress_callback=progress_callback
                )

                if clip_path:
                    _vod_clip_jobs[job_id]['status'] = 'completed'
                    _vod_clip_jobs[job_id]['clip_path'] = clip_path
                    _vod_clip_jobs[job_id]['message'] = 'Clip created successfully'
                    _vod_clip_jobs[job_id]['progress'] = 100

                    # Register clip in database
                    register_clip(clip_path, streamer, 'vod_manual')
                else:
                    _vod_clip_jobs[job_id]['status'] = 'failed'
                    _vod_clip_jobs[job_id]['message'] = 'Failed to create clip'
            except Exception as e:
                _vod_clip_jobs[job_id]['status'] = 'failed'
                _vod_clip_jobs[job_id]['message'] = str(e)

        thread = threading.Thread(target=clip_worker, daemon=True)
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Clip creation started',
            'estimated_duration': duration
        }), 202

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to start clipping: {str(e)}',
            'code': 'CLIP_ERROR'
        }), 500


@api_bp.route('/vods/clip/status/<job_id>', methods=['GET'])
def get_clip_job_status(job_id):
    """Get the status of a VOD clipping job."""
    if job_id not in _vod_clip_jobs:
        return jsonify({
            'success': False,
            'error': 'Job not found',
            'code': 'NOT_FOUND'
        }), 404

    job = _vod_clip_jobs[job_id]

    response = {
        'success': True,
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message']
    }

    if job['status'] == 'completed' and job['clip_path']:
        clip_path = Path(job['clip_path'])
        response['clip'] = {
            'filename': clip_path.name,
            'url': f'/clips/{clip_path.name}',
            'size_mb': round(clip_path.stat().st_size / (1024 * 1024), 2) if clip_path.exists() else 0
        }

    return jsonify(response), 200


@api_bp.route('/vods/analyze/<vod_id>', methods=['POST'])
def analyze_vod_highlights(vod_id):
    """
    Analyze a VOD for highlight moments (Premium - costs 1 credit).

    Request body:
        duration: VOD duration in seconds (optional, for better analysis)
        start_time: VOD start time ISO string (optional)
    """
    data = request.get_json() or {}

    try:
        analyzer = get_chat_analyzer()
        clipper = get_vod_clipper()

        # Get VOD details if not provided
        vod_duration = data.get('duration', 0)
        vod_start_time = data.get('start_time')

        if not vod_duration:
            vod = clipper.get_vod_details(vod_id)
            if vod:
                vod_duration = vod.duration
                vod_start_time = vod.created_at

        # Analyze the VOD
        highlights = analyzer.analyze_vod(
            vod_id=vod_id,
            vod_duration=vod_duration,
            vod_start_time=vod_start_time
        )

        return jsonify({
            'success': True,
            'vod_id': vod_id,
            'highlights': [h.to_dict() for h in highlights],
            'total': len(highlights),
            'credits_used': 1,
            'note': 'Premium feature - 1 credit used'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to analyze VOD: {str(e)}',
            'code': 'ANALYZE_ERROR'
        }), 500


@api_bp.route('/vods/clip/batch', methods=['POST'])
def batch_clip_vod():
    """
    Create multiple clips from detected highlights (Premium feature).

    Request body:
        vod_id: The VOD ID
        streamer: Streamer name
        highlights: List of highlight objects with timestamp_seconds
        clip_duration: Duration of each clip in seconds (default: 45)
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'Missing request body',
            'code': 'INVALID_REQUEST'
        }), 400

    vod_id = data.get('vod_id')
    streamer = data.get('streamer', '').strip().lower()
    highlights = data.get('highlights', [])
    clip_duration = data.get('clip_duration', 45)

    if not vod_id or not highlights or not streamer:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: vod_id, streamer, highlights',
            'code': 'INVALID_REQUEST'
        }), 400

    # Start batch clipping in background
    import uuid
    batch_id = str(uuid.uuid4())[:8]

    _vod_clip_jobs[f'batch_{batch_id}'] = {
        'status': 'processing',
        'total': len(highlights),
        'completed': 0,
        'failed': 0,
        'clips': []
    }

    def batch_worker():
        clipper = get_vod_clipper()
        job = _vod_clip_jobs[f'batch_{batch_id}']

        for highlight in highlights:
            timestamp = highlight.get('timestamp_seconds', 0)
            trigger_type = highlight.get('trigger_type', 'highlight')

            # Calculate start/end (center the clip around the highlight)
            half_duration = clip_duration // 2
            start_seconds = max(0, timestamp - half_duration)
            end_seconds = timestamp + half_duration

            try:
                clip_path = clipper.create_clip(
                    vod_id=vod_id,
                    start_time=start_seconds,
                    end_time=end_seconds,
                    streamer=streamer
                )

                if clip_path:
                    job['completed'] += 1
                    job['clips'].append({
                        'timestamp': timestamp,
                        'path': clip_path,
                        'filename': Path(clip_path).name
                    })
                    register_clip(clip_path, streamer, f'vod_auto_{trigger_type}')
                else:
                    job['failed'] += 1
            except Exception:
                job['failed'] += 1

        job['status'] = 'completed'

    thread = threading.Thread(target=batch_worker, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'message': f'Started batch clipping of {len(highlights)} highlights',
        'total': len(highlights)
    }), 202


@api_bp.route('/vods/clip/batch/<batch_id>', methods=['GET'])
def get_batch_clip_status(batch_id):
    """Get status of a batch clipping job."""
    job_key = f'batch_{batch_id}'

    if job_key not in _vod_clip_jobs:
        return jsonify({
            'success': False,
            'error': 'Batch job not found',
            'code': 'NOT_FOUND'
        }), 404

    job = _vod_clip_jobs[job_key]

    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'status': job['status'],
        'total': job['total'],
        'completed': job['completed'],
        'failed': job['failed'],
        'clips': job['clips']
    }), 200


# ==================
# Clip Editor API
# ==================

# Track trim jobs
_trim_jobs = {}


@api_bp.route('/clips/trim', methods=['POST'])
def trim_clip_endpoint():
    """
    Trim a clip by setting start/end points.

    Request body:
        filename: The clip filename to trim
        start_time: Start time (seconds or HH:MM:SS format)
        end_time: End time (seconds or HH:MM:SS format)
        output_name: Optional custom output filename
        reencode: Optional boolean to force re-encoding (default: false)

    Returns:
        Job ID for tracking progress
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'error': 'Missing request body',
            'code': 'INVALID_REQUEST'
        }), 400

    # Validate required fields
    required_fields = ['filename', 'start_time', 'end_time']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}',
                'code': 'INVALID_REQUEST'
            }), 400

    filename = data['filename']
    start_time = data['start_time']
    end_time = data['end_time']
    output_name = data.get('output_name')
    reencode = data.get('reencode', False)

    # Find the clip file
    clip_path = find_clip_path(filename)
    if not clip_path:
        return jsonify({
            'success': False,
            'error': 'Clip not found',
            'code': 'NOT_FOUND'
        }), 404

    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())[:8]

    # Initialize job tracking
    _trim_jobs[job_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'Starting trim operation...',
        'output_path': None,
        'output_filename': None,
        'duration': None
    }

    def progress_callback(message, progress):
        _trim_jobs[job_id]['message'] = message
        _trim_jobs[job_id]['progress'] = progress

    def trim_worker():
        from src.clip.editor import trim_clip_api

        try:
            result = trim_clip_api(
                input_path=str(clip_path),
                start_time=start_time,
                end_time=end_time,
                output_name=output_name,
                output_dir=str(clip_path.parent),
                reencode=reencode,
                progress_callback=progress_callback
            )

            if result['success']:
                _trim_jobs[job_id]['status'] = 'completed'
                _trim_jobs[job_id]['output_path'] = result['output_path']
                _trim_jobs[job_id]['output_filename'] = result['output_filename']
                _trim_jobs[job_id]['duration'] = result['duration']
                _trim_jobs[job_id]['message'] = 'Trim complete!'
                _trim_jobs[job_id]['progress'] = 100
            else:
                _trim_jobs[job_id]['status'] = 'failed'
                _trim_jobs[job_id]['message'] = result.get('error', 'Unknown error')

        except Exception as e:
            _trim_jobs[job_id]['status'] = 'failed'
            _trim_jobs[job_id]['message'] = str(e)

    # Start trim in background thread
    thread = threading.Thread(target=trim_worker, daemon=True)
    thread.start()

    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Trim operation started'
    }), 202


@api_bp.route('/clips/trim/status/<job_id>', methods=['GET'])
def get_trim_status(job_id):
    """Get the status of a trim job."""
    if job_id not in _trim_jobs:
        return jsonify({
            'success': False,
            'error': 'Job not found',
            'code': 'NOT_FOUND'
        }), 404

    job = _trim_jobs[job_id]

    response = {
        'success': True,
        'job_id': job_id,
        'status': job['status'],
        'progress': job['progress'],
        'message': job['message']
    }

    if job['status'] == 'completed' and job['output_path']:
        output_path = Path(job['output_path'])
        response['clip'] = {
            'filename': job['output_filename'],
            'url': f'/clips/{job["output_filename"]}',
            'duration': job['duration'],
            'size_mb': round(output_path.stat().st_size / (1024 * 1024), 2) if output_path.exists() else 0
        }

    return jsonify(response), 200


@api_bp.route('/clips/<filename>/metadata', methods=['GET'])
def get_clip_metadata(filename):
    """Get metadata for a clip (duration, dimensions, etc.)."""
    clip_path = find_clip_path(filename)

    if not clip_path:
        return jsonify({
            'success': False,
            'error': 'Clip not found',
            'code': 'NOT_FOUND'
        }), 404

    from src.clip.editor import get_video_metadata

    try:
        metadata = get_video_metadata(str(clip_path))

        return jsonify({
            'success': True,
            'filename': filename,
            'metadata': metadata
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get metadata: {str(e)}',
            'code': 'METADATA_ERROR'
        }), 500
