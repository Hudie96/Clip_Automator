"""
Thread-safe shared statistics for real-time dashboard updates.
Singleton pattern ensures all parts of the application share the same stats.
"""

import threading
from typing import Dict, List, Optional
from datetime import datetime, date


class SharedStats:
    """Singleton class to store and manage real-time statistics."""

    _instance: Optional['SharedStats'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the shared stats storage."""
        # Thread lock for all operations
        self._data_lock = threading.Lock()

        # Current viewer counts per streamer
        self.viewer_counts: Dict[str, int] = {}

        # Chat message velocity (messages per minute) per streamer
        self.chat_velocities: Dict[str, float] = {}

        # Recent trigger events (last 20)
        self.recent_triggers: List[dict] = []

        # Recording status per streamer
        self.recording_status: Dict[str, bool] = {}

        # Clips created today per streamer (for display, not limiting)
        self.clips_today: Dict[str, int] = {}
        self.clips_date: Optional[datetime] = None

    def update_viewers(self, streamer: str, count: int):
        """Update viewer count for a streamer."""
        with self._data_lock:
            self.viewer_counts[streamer] = count

    def update_velocity(self, streamer: str, velocity: float):
        """Update chat velocity for a streamer."""
        with self._data_lock:
            self.chat_velocities[streamer] = round(velocity, 2)

    def add_trigger(self, streamer: str, trigger_type: str, details: dict = None):
        """
        Add a new trigger event to recent triggers.
        Keeps only the last 20 events.

        Args:
            streamer: Name of the streamer
            trigger_type: Type of trigger (e.g., 'viewer_spike', 'chat_burst')
            details: Additional details about the trigger
        """
        with self._data_lock:
            trigger_event = {
                'streamer': streamer,
                'trigger_type': trigger_type,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }

            # Add to front of list
            self.recent_triggers.insert(0, trigger_event)

            # Keep only last 20
            if len(self.recent_triggers) > 20:
                self.recent_triggers = self.recent_triggers[:20]

    def update_recording_status(self, streamer: str, is_recording: bool):
        """Update recording status for a streamer."""
        with self._data_lock:
            self.recording_status[streamer] = is_recording

    def increment_clips_today(self, streamer: str):
        """Increment the clip count for today for a streamer."""
        with self._data_lock:
            today = date.today()
            # Reset counts if it's a new day
            if self.clips_date != today:
                self.clips_today.clear()
                self.clips_date = today
            self.clips_today[streamer] = self.clips_today.get(streamer, 0) + 1

    def get_clips_today(self, streamer: str) -> int:
        """Get the number of clips created today for a streamer."""
        with self._data_lock:
            today = date.today()
            if self.clips_date != today:
                return 0
            return self.clips_today.get(streamer, 0)

    def get_all_stats(self) -> dict:
        """
        Get all current statistics in a thread-safe manner.

        Returns:
            Dictionary containing all current stats in format expected by dashboard
        """
        with self._data_lock:
            # Build streamer_stats in format dashboard expects
            streamer_stats = {}
            all_streamers = set(self.viewer_counts.keys()) | set(self.chat_velocities.keys()) | set(self.recording_status.keys())

            today = date.today()
            for streamer in all_streamers:
                clips_count = 0
                if self.clips_date == today:
                    clips_count = self.clips_today.get(streamer, 0)

                streamer_stats[streamer] = {
                    'viewers': self.viewer_counts.get(streamer, 0),
                    'chat_velocity': self.chat_velocities.get(streamer, 0.0),
                    'recording': self.recording_status.get(streamer, False),
                    'clips_today': clips_count
                }

            return {
                'streamer_stats': streamer_stats,
                'recent_triggers': self.recent_triggers.copy(),
                'last_updated': datetime.now().isoformat()
            }

    def clear_streamer_stats(self, streamer: str):
        """Clear all stats for a specific streamer (e.g., when stream ends)."""
        with self._data_lock:
            self.viewer_counts.pop(streamer, None)
            self.chat_velocities.pop(streamer, None)
            self.recording_status.pop(streamer, None)

    def reset_all(self):
        """Reset all statistics (useful for testing or maintenance)."""
        with self._data_lock:
            self.viewer_counts.clear()
            self.chat_velocities.clear()
            self.recent_triggers.clear()
            self.recording_status.clear()
            self.clips_today.clear()
            self.clips_date = None


# Global instance for easy import
shared_stats = SharedStats()
