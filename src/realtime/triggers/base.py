"""
Base trigger class for clip detection.

All triggers inherit from this and implement the same interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
import threading


@dataclass
class TriggerEvent:
    """Represents a detected moment that should create a clip."""
    trigger_type: str          # "viewer_spike", "chat_velocity", "keyword"
    timestamp: datetime        # When the trigger fired
    data: dict                 # Trigger-specific data (viewer_count, keywords, etc.)
    confidence: float = 1.0    # How confident we are (0-1)

    def __str__(self):
        return f"[{self.trigger_type}] {self.data}"


class BaseTrigger(ABC):
    """
    Base class for all clip triggers.

    Subclasses must implement:
    - start(): Begin monitoring
    - stop(): Stop monitoring
    - _check(): Internal check logic (called by monitoring loop)
    """

    def __init__(self, name: str, callback: Callable[[TriggerEvent], None] = None):
        self.name = name
        self.callback = callback
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def set_callback(self, callback: Callable[[TriggerEvent], None]):
        """Set the callback function for when a trigger fires."""
        self.callback = callback

    def fire(self, event: TriggerEvent):
        """Fire a trigger event - ALWAYS calls callback, no cooldown here.

        Cooldown logic should be handled by the callback (e.g., for clip creation)
        so that all trigger events are visible for monitoring.
        """
        print(f"[{self.name}] TRIGGERED: {event}")

        if self.callback:
            self.callback(event)

    @abstractmethod
    def start(self):
        """Start the trigger monitoring."""
        pass

    @abstractmethod
    def stop(self):
        """Stop the trigger monitoring."""
        pass

    def start_threaded(self):
        """Start the trigger in a background thread."""
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self.start, daemon=True)
        self._thread.start()

    def is_running(self) -> bool:
        """Check if the trigger is currently running."""
        return self.running
