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

    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moments_processed
        ON moments(processed)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_moments_session
        ON moments(session_id)
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


if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
    print("Database ready!")
