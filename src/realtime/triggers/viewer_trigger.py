"""
Viewer count trigger - detects viewer spikes via REST API.
"""

import cloudscraper
import time
from datetime import datetime
from collections import deque
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from config.settings import (
    SPIKE_THRESHOLD,
    POLL_INTERVAL,
    BASELINE_WINDOW,
    KICK_API_BASE
)
from .base import BaseTrigger, TriggerEvent


class ViewerTrigger(BaseTrigger):
    """
    Monitors viewer count via Kick REST API.
    Fires when viewers exceed baseline × threshold.
    """

    def __init__(self, streamer: str, callback=None):
        super().__init__(name="viewer", callback=callback)
        self.streamer = streamer
        self.api_url = f"{KICK_API_BASE}/{streamer}"

        # Rolling window for baseline
        self.viewer_history = deque(maxlen=int(BASELINE_WINDOW / POLL_INTERVAL))

        # Use cloudscraper to bypass Cloudflare protection
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

        # Stream info
        self.is_live = False
        self.channel_id: Optional[int] = None
        self.chatroom_id: Optional[int] = None

    def get_stream_data(self) -> Optional[dict]:
        """Fetch current stream data from Kick API."""
        try:
            response = self.scraper.get(self.api_url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[viewer] API error: {e}")
            return None

    def calculate_baseline(self) -> float:
        """Calculate rolling average of viewer count."""
        if not self.viewer_history:
            return 0
        return sum(self.viewer_history) / len(self.viewer_history)

    def start(self):
        """Start monitoring viewer counts."""
        self.running = True
        print(f"[viewer] Starting viewer monitor for {self.streamer}")
        print(f"[viewer] Spike threshold: {SPIKE_THRESHOLD}x baseline")

        while self.running:
            data = self.get_stream_data()

            if not data:
                time.sleep(POLL_INTERVAL)
                continue

            # Extract channel/chatroom IDs on first successful call
            if not self.channel_id:
                self.channel_id = data.get('id')
                chatroom = data.get('chatroom', {})
                self.chatroom_id = chatroom.get('id')
                print(f"[viewer] Channel ID: {self.channel_id}, Chatroom ID: {self.chatroom_id}")

            # Check if live
            livestream = data.get('livestream')
            is_live = livestream and livestream.get('is_live', False)

            if not is_live:
                if self.is_live:
                    print(f"[viewer] Stream went offline")
                self.is_live = False
                self.viewer_history.clear()
                time.sleep(POLL_INTERVAL)
                continue

            if not self.is_live:
                print(f"[viewer] Stream is LIVE!")
                self.is_live = True

            # Get viewer count
            viewers = livestream.get('viewer_count', 0)
            self.viewer_history.append(viewers)
            baseline = self.calculate_baseline()

            # Check for spike
            if baseline > 0:
                ratio = viewers / baseline
                print(f"[viewer] Viewers: {viewers:,} | Baseline: {baseline:.0f} | Ratio: {ratio:.1f}x")

                if ratio >= SPIKE_THRESHOLD:
                    event = TriggerEvent(
                        trigger_type="viewer_spike",
                        timestamp=datetime.now(),
                        data={
                            "viewer_count": viewers,
                            "baseline": int(baseline),
                            "ratio": round(ratio, 2)
                        },
                        confidence=min(ratio / SPIKE_THRESHOLD, 1.0)
                    )
                    self.fire(event)

                    # Reset baseline to prevent repeat triggers
                    for _ in range(len(self.viewer_history)):
                        self.viewer_history.append(viewers)
            else:
                print(f"[viewer] Viewers: {viewers:,} (building baseline...)")

            time.sleep(POLL_INTERVAL)

    def stop(self):
        """Stop monitoring."""
        self.running = False
        print(f"[viewer] Stopped")

    def get_chatroom_id(self) -> Optional[int]:
        """Get the chatroom ID (needed for chat trigger)."""
        if self.chatroom_id:
            return self.chatroom_id

        # Fetch if not cached
        data = self.get_stream_data()
        if data:
            self.chatroom_id = data.get('chatroom', {}).get('id')
        return self.chatroom_id
