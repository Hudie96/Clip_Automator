"""
SQLite database schema and utilities for clip coordination.
"""

import sqlite3
import os
from datetime import datetime

# Add parent directory to path for config import
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from config.settings import DB_PATH


def get_connection():
    """Get a connection to the SQLite database."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Sessions table - tracks each stream recording
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            streamer TEXT NOT NULL,
            started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            ended_at DATETIME,
            recording_path TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Moments table - detected viral moments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            stream_elapsed_seconds REAL,
            viewer_count INTEGER,
            baseline_viewers INTEGER,
            spike_ratio REAL,
            processed BOOLEAN DEFAULT 0,
            clip_path TEXT,
            trigger_type TEXT,
            trigger_data TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    # Migration: Add trigger_type and trigger_data columns if they don't exist
    # This handles databases created before these columns were added
    cursor.execute("PRAGMA table_info(moments)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'trigger_type' not in columns:
        cursor.execute("ALTER TABLE moments ADD COLUMN trigger_type TEXT")
        print("Added trigger_type column to moments table")

    if 'trigger_data' not in columns:
        cursor.execute("ALTER TABLE moments ADD COLUMN trigger_data TEXT")
        print("Added trigger_data column to moments table")

    # Clips table - tracks clip review status
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clip_path TEXT UNIQUE NOT NULL,
            streamer TEXT NOT NULL,
            trigger_type TEXT,
            status TEXT DEFAULT 'pending',
            reviewed_at DATETIME,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moments_processed
        ON moments(processed)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moments_session
        ON moments(session_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_clips_status
        ON clips(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_clips_streamer
        ON clips(streamer)
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def start_session(streamer: str, recording_path: str = None) -> int:
    """Start a new monitoring session. Returns session ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions (streamer, recording_path)
        VALUES (?, ?)
    """, (streamer, recording_path))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return session_id


def end_session(session_id: int):
    """Mark a session as ended."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET ended_at = CURRENT_TIMESTAMP, is_active = 0
        WHERE id = ?
    """, (session_id,))

    conn.commit()
    conn.close()


def log_moment(
    session_id: int,
    stream_elapsed_seconds: float,
    viewer_count: int,
    baseline_viewers: int,
    spike_ratio: float,
    trigger_type: str = None,
    trigger_data: str = None
) -> int:
    """Log a detected viral moment. Returns moment ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO moments
        (session_id, stream_elapsed_seconds, viewer_count, baseline_viewers, spike_ratio, trigger_type, trigger_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, stream_elapsed_seconds, viewer_count, baseline_viewers, spike_ratio, trigger_type, trigger_data))

    moment_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return moment_id


def get_unprocessed_moments(session_id: int = None) -> list:
    """Get all moments that haven't been clipped yet."""
    conn = get_connection()
    cursor = conn.cursor()

    if session_id:
        cursor.execute("""
            SELECT m.*, s.recording_path
            FROM moments m
            JOIN sessions s ON m.session_id = s.id
            WHERE m.processed = 0 AND m.session_id = ?
            ORDER BY m.stream_elapsed_seconds
        """, (session_id,))
    else:
        cursor.execute("""
            SELECT m.*, s.recording_path
            FROM moments m
            JOIN sessions s ON m.session_id = s.id
            WHERE m.processed = 0
            ORDER BY m.session_id, m.stream_elapsed_seconds
        """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def mark_moment_processed(moment_id: int, clip_path: str):
    """Mark a moment as processed and store the clip path."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE moments
        SET processed = 1, clip_path = ?
        WHERE id = ?
    """, (clip_path, moment_id))

    conn.commit()
    conn.close()


def update_session_recording(session_id: int, recording_path: str):
    """Update the recording path for a session."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET recording_path = ?
        WHERE id = ?
    """, (recording_path, session_id))

    conn.commit()
    conn.close()


def get_session_stats(session_id: int) -> dict:
    """Get statistics for a session."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total_moments,
            SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_moments,
            AVG(spike_ratio) as avg_spike_ratio,
            MAX(viewer_count) as peak_viewers
        FROM moments
        WHERE session_id = ?
    """, (session_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else {}


# ==================
# Clip Review Functions
# ==================

def register_clip(clip_path: str, streamer: str, trigger_type: str = None) -> int:
    """Register a new clip as pending review. Returns clip ID."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO clips (clip_path, streamer, trigger_type, status)
            VALUES (?, ?, ?, 'pending')
        """, (clip_path, streamer, trigger_type))
        clip_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        # Clip already exists, get its ID
        cursor.execute("SELECT id FROM clips WHERE clip_path = ?", (clip_path,))
        row = cursor.fetchone()
        clip_id = row['id'] if row else None
    finally:
        conn.close()

    return clip_id


def get_pending_clips(streamer: str = None, limit: int = 50) -> list:
    """Get clips pending review, optionally filtered by streamer."""
    conn = get_connection()
    cursor = conn.cursor()

    if streamer:
        cursor.execute("""
            SELECT * FROM clips
            WHERE status = 'pending' AND streamer = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (streamer, limit))
    else:
        cursor.execute("""
            SELECT * FROM clips
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_clip_by_id(clip_id: int) -> dict:
    """Get a clip by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clips WHERE id = ?", (clip_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def approve_clip(clip_id: int, notes: str = None) -> bool:
    """Mark a clip as approved."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clips
        SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP, notes = ?
        WHERE id = ?
    """, (notes, clip_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def reject_clip(clip_id: int, notes: str = None) -> bool:
    """Mark a clip as rejected (queued for deletion)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clips
        SET status = 'rejected', reviewed_at = CURRENT_TIMESTAMP, notes = ?
        WHERE id = ?
    """, (notes, clip_id))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_clip_record(clip_id: int) -> bool:
    """Delete a clip record from the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM clips WHERE id = ?", (clip_id,))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_rejected_clips(older_than_hours: int = 24) -> list:
    """Get rejected clips older than specified hours for cleanup."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM clips
        WHERE status = 'rejected'
        AND reviewed_at < datetime('now', ? || ' hours')
    """, (-older_than_hours,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_clip_stats() -> dict:
    """Get overall clip statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected
        FROM clips
    """)

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print("Database ready!")
