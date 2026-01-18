"""
Chat trigger - detects viral moments via WebSocket chat analysis.

Monitors:
- Chat velocity (messages per second)
- Keyword spam ("CLIP", "OMG", etc.)
- Emote spam
"""

import json
import time
import threading
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Callable
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from config.settings import (
    PUSHER_WS_URL,
    CHAT_VELOCITY_THRESHOLD,
    CHAT_WINDOW_SECONDS,
    CLIP_KEYWORDS,
    KEYWORD_THRESHOLD,
    EMOTE_SPAM_THRESHOLD,
    WS_RECONNECT_DELAY,
    WS_MAX_RECONNECT_ATTEMPTS,
    DYNAMIC_THRESHOLD_ENABLED,
    BASELINE_WINDOW_MINUTES,
    COMBO_WINDOW_SECONDS
)
from .base import BaseTrigger, TriggerEvent
from .dynamic_baseline import DynamicBaseline
from .excitement_detector import ExcitementDetector
from .combo_trigger import ComboTrigger
from src.web.live_stats import shared_stats

# Try to import websocket
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("[chat] WARNING: websocket-client not installed. Run: pip install websocket-client")


class ChatTrigger(BaseTrigger):
    """
    Monitors chat via Kick's Pusher WebSocket.
    Fires on chat velocity spikes, keyword spam, or emote spam.
    """

    def __init__(self, chatroom_id: int, callback: Callable = None, streamer: str = None):
        super().__init__(name="chat", callback=callback)
        self.chatroom_id = chatroom_id
        self.streamer = streamer  # For updating shared stats
        self.ws: Optional[websocket.WebSocketApp] = None

        # Message tracking
        self.message_times = deque()  # Timestamps of recent messages
        self.keyword_counts = {}      # Keyword -> count in window
        self.emote_counts = {}        # Emote -> count in window

        # Initialize smart trigger components
        if DYNAMIC_THRESHOLD_ENABLED:
            self.dynamic_baseline = DynamicBaseline(
                channel_id=str(chatroom_id),
                window_duration_seconds=BASELINE_WINDOW_MINUTES * 60
            )
        else:
            self.dynamic_baseline = None

        self.excitement_detector = ExcitementDetector()
        self.combo_trigger = ComboTrigger(window_seconds=COMBO_WINDOW_SECONDS)

        # Reconnection
        self.reconnect_attempts = 0

    def _on_open(self, ws):
        """Called when WebSocket connection opens."""
        print(f"[chat] Connected to Pusher WebSocket")
        self.reconnect_attempts = 0

        # Subscribe to chatroom channel
        subscribe_msg = {
            "event": "pusher:subscribe",
            "data": {
                "channel": f"chatrooms.{self.chatroom_id}.v2"
            }
        }
        ws.send(json.dumps(subscribe_msg))
        print(f"[chat] Subscribed to chatrooms.{self.chatroom_id}.v2")

    def _on_message(self, ws, message):
        """Called when a message is received."""
        try:
            msg = json.loads(message)
            event = msg.get('event', '')

            # Handle chat messages
            if event == 'App\\Events\\ChatMessageEvent':
                data_str = msg.get('data', '{}')
                data = json.loads(data_str) if isinstance(data_str, str) else data_str
                self._process_chat_message(data)

            # Handle subscription success
            elif event == 'pusher_internal:subscription_succeeded':
                print(f"[chat] Subscription confirmed")

            # Handle pusher ping
            elif event == 'pusher:ping':
                ws.send(json.dumps({"event": "pusher:pong", "data": {}}))

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[chat] Error processing message: {e}")

    def _on_error(self, ws, error):
        """Called on WebSocket error."""
        print(f"[chat] WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket closes."""
        print(f"[chat] WebSocket closed (code: {close_status_code})")

        if self.running and self.reconnect_attempts < WS_MAX_RECONNECT_ATTEMPTS:
            self.reconnect_attempts += 1
            print(f"[chat] Reconnecting in {WS_RECONNECT_DELAY}s (attempt {self.reconnect_attempts})...")
            time.sleep(WS_RECONNECT_DELAY)
            self._connect()

    def _process_chat_message(self, data: dict):
        """Process an incoming chat message."""
        now = datetime.now()
        content = data.get('content', '')

        # Track message time
        self.message_times.append(now)

        # Clean old messages from window
        cutoff = now - timedelta(seconds=CHAT_WINDOW_SECONDS)
        while self.message_times and self.message_times[0] < cutoff:
            self.message_times.popleft()

        # Calculate velocity
        velocity = len(self.message_times) / CHAT_WINDOW_SECONDS

        # Update shared stats for dashboard (convert to messages per minute for display)
        if self.streamer:
            shared_stats.update_velocity(self.streamer, velocity * 60)

        # Update dynamic baseline and check for spike
        if self.dynamic_baseline:
            self.dynamic_baseline.add_sample(velocity)
            is_spike = self.dynamic_baseline.is_spike(velocity)
        else:
            # Fallback to static threshold
            is_spike = velocity >= CHAT_VELOCITY_THRESHOLD

        if is_spike:
            threshold = self.dynamic_baseline.get_threshold() if self.dynamic_baseline else CHAT_VELOCITY_THRESHOLD
            event = TriggerEvent(
                trigger_type="chat_velocity",
                timestamp=now,
                data={
                    "velocity": round(velocity, 2),
                    "threshold": round(threshold, 2) if threshold else CHAT_VELOCITY_THRESHOLD,
                    "message_count": len(self.message_times),
                    "window_seconds": CHAT_WINDOW_SECONDS,
                    "dynamic": DYNAMIC_THRESHOLD_ENABLED
                },
                confidence=min(velocity / max(threshold, CHAT_VELOCITY_THRESHOLD), 1.0) if threshold else min(velocity / CHAT_VELOCITY_THRESHOLD, 1.0)
            )
            self.fire(event)
            self.combo_trigger.record_event("chat_velocity", now)

        # Check for excitement indicators in message
        excitement_result = self.excitement_detector.check_message(content)

        # Check keywords (enhanced with excitement detector)
        for keyword in CLIP_KEYWORDS:
            if keyword.upper() in content.upper():
                self.keyword_counts[keyword] = self.keyword_counts.get(keyword, 0) + 1

                if self.keyword_counts[keyword] >= KEYWORD_THRESHOLD:
                    event = TriggerEvent(
                        trigger_type="keyword",
                        timestamp=now,
                        data={
                            "keyword": keyword,
                            "count": self.keyword_counts[keyword],
                            "threshold": KEYWORD_THRESHOLD,
                            "excitement_score": excitement_result.get("excitement_score", 0.0)
                        },
                        confidence=min(1.0, 0.5 + excitement_result.get("excitement_score", 0.0))
                    )
                    self.fire(event)
                    self.combo_trigger.record_event("keyword", now)
                    # Reset count after trigger
                    self.keyword_counts[keyword] = 0

        # Check for emote flood
        recent_messages = [{"text": data.get('content', '')}]  # Simplified for current message
        if self.excitement_detector.detect_emote_flood(recent_messages, window_seconds=CHAT_WINDOW_SECONDS):
            event = TriggerEvent(
                trigger_type="emote_flood",
                timestamp=now,
                data={
                    "emotes": excitement_result.get("emotes_found", []),
                    "threshold": EMOTE_SPAM_THRESHOLD
                },
                confidence=excitement_result.get("excitement_score", 0.0)
            )
            self.fire(event)
            self.combo_trigger.record_event("emote_flood", now)

        # Check for combos after recording events
        combo = self.combo_trigger.check_combo()
        if combo:
            combo_event = TriggerEvent(
                trigger_type=f"combo_{combo['combo_type']}",
                timestamp=now,
                data=combo,
                confidence=combo.get("confidence", 0.0)
            )
            self.fire(combo_event)

        # Decay keyword counts over time (simple approach)
        # Reset every window period
        if len(self.message_times) == 1:  # First message in new window
            self.keyword_counts = {}

    def _connect(self):
        """Establish WebSocket connection."""
        if not WEBSOCKET_AVAILABLE:
            print("[chat] Cannot connect - websocket-client not installed")
            return

        self.ws = websocket.WebSocketApp(
            PUSHER_WS_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        # Run in a thread
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

    def start(self):
        """Start monitoring chat."""
        if not WEBSOCKET_AVAILABLE:
            print("[chat] websocket-client not installed. Skipping chat monitoring.")
            return

        self.running = True
        print(f"[chat] Starting chat monitor for chatroom {self.chatroom_id}")
        print(f"[chat] Velocity threshold: {CHAT_VELOCITY_THRESHOLD} msg/sec")
        print(f"[chat] Keywords: {CLIP_KEYWORDS}")

        self._connect()

        # Keep the thread alive
        while self.running:
            time.sleep(1)

    def stop(self):
        """Stop monitoring chat."""
        self.running = False
        if self.ws:
            self.ws.close()
        print(f"[chat] Stopped")

    def get_stats(self) -> dict:
        """Get current monitoring stats."""
        velocity = len(self.message_times) / CHAT_WINDOW_SECONDS if self.message_times else 0
        return {
            "velocity": round(velocity, 2),
            "message_count": len(self.message_times),
            "keyword_counts": dict(self.keyword_counts)
        }
