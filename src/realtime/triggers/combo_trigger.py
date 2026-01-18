"""
Combo trigger - detects when multiple triggers fire together.

Detects high-confidence moments when multiple signals align:
- chat_velocity + keyword = "chat_combo"
- viewer_spike + chat_velocity = "hype_moment"
- keyword + emote_flood = "clip_worthy"
- Any 3+ triggers = "super_combo"

Tracks events in a sliding time window for accurate combo detection.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Callable
from .base import BaseTrigger, TriggerEvent


class ComboTrigger:
    """
    Detects when multiple trigger types fire within a time window.

    No inheritance from BaseTrigger - this is a passive analyzer that
    receives events from other triggers and checks for combinations.
    """

    # Combo definitions
    COMBOS = {
        "chat_combo": {"triggers": ["chat_velocity", "keyword"], "confidence_boost": 0.15},
        "hype_moment": {"triggers": ["viewer_spike", "chat_velocity"], "confidence_boost": 0.20},
        "clip_worthy": {"triggers": ["keyword", "emote_flood"], "confidence_boost": 0.15},
        "super_combo": {"triggers": 3, "confidence_boost": 0.30}  # 3 or more triggers
    }

    def __init__(self, window_seconds: float = 10.0, callback: Callable = None):
        """
        Initialize combo trigger.

        Args:
            window_seconds: Time window to track events (default 10)
            callback: Optional callback function for combo detection
        """
        self.window_seconds = window_seconds
        self.callback = callback

        # Event tracking: deque of (trigger_type, timestamp) tuples
        self.events = deque()

    def record_event(self, trigger_type: str, timestamp: Optional[datetime] = None):
        """
        Record a trigger event for combo detection.

        Args:
            trigger_type: Type of trigger ("chat_velocity", "keyword", "viewer_spike", "emote_flood")
            timestamp: When the event occurred (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Add event
        self.events.append((trigger_type, timestamp))

        # Clean old events outside window
        self._clean_old_events()

    def _clean_old_events(self):
        """Remove events older than the time window."""
        cutoff = datetime.now() - timedelta(seconds=self.window_seconds)

        while self.events and self.events[0][1] < cutoff:
            self.events.popleft()

    def check_combo(self) -> Optional[dict]:
        """
        Check if current events form a combo.

        Returns:
            None if no combo detected
            dict with combo info if detected:
                {
                    "combo_type": str,
                    "triggers": list[str],
                    "confidence": float,
                    "event_count": int,
                    "time_window": float
                }
        """
        # Clean old events first
        self._clean_old_events()

        if not self.events:
            return None

        # Get unique trigger types in current window
        trigger_types = set(t[0] for t in self.events)
        trigger_list = list(trigger_types)
        trigger_count = len(trigger_types)

        # Check for super_combo first (3+ different triggers)
        if trigger_count >= 3:
            combo_info = self.COMBOS["super_combo"]
            base_confidence = sum(1.0 / trigger_count for _ in range(trigger_count))
            confidence = min(base_confidence + combo_info["confidence_boost"], 1.0)

            result = {
                "combo_type": "super_combo",
                "triggers": trigger_list,
                "confidence": round(confidence, 2),
                "event_count": len(self.events),
                "time_window": self.window_seconds
            }
            self._fire_combo(result)
            return result

        # Check for specific 2-trigger combos
        for combo_name, combo_config in self.COMBOS.items():
            if combo_name == "super_combo":  # Already checked
                continue

            required_triggers = set(combo_config["triggers"])

            # Check if all required triggers are present
            if required_triggers.issubset(trigger_types):
                # Calculate base confidence from event counts
                counts = {t: 0 for t in required_triggers}
                for trigger_type, _ in self.events:
                    if trigger_type in counts:
                        counts[trigger_type] += 1

                # Average confidence per trigger type
                base_confidence = sum(min(count / 3.0, 1.0) for count in counts.values()) / len(counts)
                confidence = min(base_confidence + combo_config["confidence_boost"], 1.0)

                result = {
                    "combo_type": combo_name,
                    "triggers": trigger_list,
                    "confidence": round(confidence, 2),
                    "event_count": len(self.events),
                    "time_window": self.window_seconds
                }
                self._fire_combo(result)
                return result

        # No combo detected
        return None

    def _fire_combo(self, combo_info: dict):
        """Fire the combo callback if set."""
        if self.callback:
            self.callback(combo_info)

    def get_events(self) -> list:
        """Get current events in window (for debugging)."""
        self._clean_old_events()
        return [
            {"trigger_type": t, "timestamp": ts.isoformat()}
            for t, ts in self.events
        ]

    def get_stats(self) -> dict:
        """Get statistics about tracked events."""
        self._clean_old_events()
        trigger_types = {}

        for trigger_type, _ in self.events:
            trigger_types[trigger_type] = trigger_types.get(trigger_type, 0) + 1

        return {
            "events_in_window": len(self.events),
            "unique_triggers": len(set(t[0] for t in self.events)),
            "trigger_counts": trigger_types,
            "window_seconds": self.window_seconds
        }

    def reset(self):
        """Clear all tracked events."""
        self.events.clear()
