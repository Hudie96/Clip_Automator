"""
Thread-safe shared statistics for real-time dashboard updates.
Singleton pattern ensures all parts of the application share the same stats.
"""

import threading
from typing import Dict, List, Optional
from datetime import datetime


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
                'type': trigger_type,
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

    def get_all_stats(self) -> dict:
        """
        Get all current statistics in a thread-safe manner.

        Returns:
            Dictionary containing all current stats
        """
        with self._data_lock:
            return {
                'viewer_counts': self.viewer_counts.copy(),
                'chat_velocities': self.chat_velocities.copy(),
                'recent_triggers': self.recent_triggers.copy(),
                'recording_status': self.recording_status.copy(),
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


# Global instance for easy import
shared_stats = SharedStats()
