"""
REST API endpoints for clip management.
Handles clip deletion, renaming, and favorite management.
"""

import json
from pathlib import Path
from flask import Blueprint, request, jsonify

# Get project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CLIPS_DIR = PROJECT_ROOT / "clips"
DATA_DIR = PROJECT_ROOT / "data"
FAVORITES_FILE = DATA_DIR / "favorites.json"

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
