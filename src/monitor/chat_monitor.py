"""
Real-time chat monitor for detecting viral moments via chat activity.

Usage:
    python src/monitor/chat_monitor.py --streamer clavicular

This script:
1. Connects to Kick's chat via Pusher WebSocket
2. Tracks message velocity (messages/second)
3. Detects keyword spikes (CLIP, INSANE, etc.)
4. Logs detected moments to SQLite for later clipping
"""

import argparse
import requests
import time
import signal
import sys
import os
import json
import threading
from datetime import datetime
from collections import deque

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import websocket
except ImportError:
    print("[ERROR] websocket-client not installed. Install with: pip install websocket-client")
    sys.exit(1)

from config.settings import (
    CHAT_VELOCITY_THRESHOLD,
    CHAT_WINDOW_SECONDS,
    CLIP_KEYWORDS,
    KEYWORD_THRESHOLD,
    PUSHER_WS_URL,
    DEFAULT_STREAMER,
    WS_RECONNECT_DELAY,
    WS_MAX_RECONNECT_ATTEMPTS,
    KICK_API_BASE,
)
from src.db.schema import init_db, start_session, end_session, log_moment


class ChatMonitor:
    def __init__(self, streamer: str):
        self.streamer = streamer
        self.session_id = None
        self.running = False
        self.ws = None
        self.reconnect_attempts = 0
        self.chatroom_id = None
        self.stream_start = None

        # Message tracking
        self.message_times = deque()  # Timestamps of messages in window
        self.keyword_occurrences = deque()  # Keyword timestamps in window

        # Headers to avoid 403 blocks
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://kick.com/',
        }

    def get_chatroom_id(self) -> str:
        """Fetch chatroom ID from Kick API."""
        try:
            url = f"{KICK_API_BASE}/{self.streamer}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            chatroom = data.get('chatroom', {})
            chatroom_id = chatroom.get('id')

            if not chatroom_id:
                print(f"[ERROR] Could not find chatroom_id in API response")
                return None

            return str(chatroom_id)
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch chatroom ID: {e}")
            return None

    def get_stream_status(self) -> bool:
        """Check if stream is currently live."""
        try:
            url = f"{KICK_API_BASE}/{self.streamer}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            livestream = data.get('livestream', {})
            is_live = livestream.get('is_live', False)

            return is_live
        except requests.RequestException as e:
            print(f"[ERROR] Failed to check stream status: {e}")
            return False

    def connect_websocket(self):
        """Connect to Pusher WebSocket for chat messages."""
        try:
            print(f"[Chat] Connecting to WebSocket...")

            def on_open(ws):
                print(f"[Chat] WebSocket connected")
                self.reconnect_attempts = 0
                # Subscribe to chat channel
                subscribe_msg = {
                    "event": "pusher:subscribe",
                    "data": {
                        "channel": f"chat-{self.chatroom_id}"
                    }
                }
                ws.send(json.dumps(subscribe_msg))
                print(f"[Chat] Subscribed to chat-{self.chatroom_id}")

            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    self.handle_message(data)
                except json.JSONDecodeError:
                    pass  # Ignore malformed messages
                except Exception as e:
                    print(f"[ERROR] Error processing message: {e}")

            def on_error(ws, error):
                print(f"[ERROR] WebSocket error: {error}")

            def on_close(ws, close_status_code, close_msg):
                print(f"[Chat] WebSocket closed (code: {close_status_code})")

            self.ws = websocket.WebSocketApp(
                PUSHER_WS_URL,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            # Run in separate thread
            ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            ws_thread.start()

            # Wait for connection
            time.sleep(2)
            return self.ws is not None

        except Exception as e:
            print(f"[ERROR] Failed to connect WebSocket: {e}")
            return False

    def handle_message(self, data: dict):
        """Process incoming chat message."""
        event = data.get('event')

        # Ignore non-message events
        if event != 'message':
            return

        try:
            message_data = json.loads(data.get('data', '{}'))
        except (json.JSONDecodeError, TypeError):
            return

        # Extract message content
        content = message_data.get('content', '').upper()

        if not content:
            return

        current_time = time.time()

        # Record message timestamp
        self.message_times.append(current_time)

        # Check for keywords
        keyword_found = False
        for keyword in CLIP_KEYWORDS:
            if keyword in content:
                keyword_found = True
                self.keyword_occurrences.append(current_time)
                break

        # Clean up old entries outside window
        self.prune_old_messages(current_time)

        # Check for velocity spike
        self.check_velocity(current_time)

        # Check for keyword spike
        self.check_keywords(current_time)

    def prune_old_messages(self, current_time: float):
        """Remove messages older than the window."""
        cutoff_time = current_time - CHAT_WINDOW_SECONDS

        # Prune message times
        while self.message_times and self.message_times[0] < cutoff_time:
            self.message_times.popleft()

        # Prune keyword occurrences
        while self.keyword_occurrences and self.keyword_occurrences[0] < cutoff_time:
            self.keyword_occurrences.popleft()

    def check_velocity(self, current_time: float):
        """Check if message velocity exceeds threshold."""
        if not self.message_times:
            return

        # Calculate velocity (messages per second)
        time_span = current_time - self.message_times[0]
        if time_span < 1:
            return

        velocity = len(self.message_times) / time_span

        # Trigger if velocity exceeds threshold
        if velocity >= CHAT_VELOCITY_THRESHOLD:
            self.log_moment_triggered(
                trigger_type="VELOCITY",
                velocity=velocity,
                keyword_count=len(self.keyword_occurrences)
            )

    def check_keywords(self, current_time: float):
        """Check if keyword mentions exceed threshold."""
        if len(self.keyword_occurrences) >= KEYWORD_THRESHOLD:
            velocity = len(self.message_times) / (current_time - self.message_times[0]) if self.message_times else 0

            self.log_moment_triggered(
                trigger_type="KEYWORDS",
                velocity=velocity,
                keyword_count=len(self.keyword_occurrences)
            )

    def log_moment_triggered(self, trigger_type: str, velocity: float, keyword_count: int):
        """Log a detected moment to the database."""
        if not self.session_id:
            return

        # Calculate stream elapsed time (approximate)
        elapsed_seconds = time.time() - self.stream_start if self.stream_start else 0

        moment_id = log_moment(
            session_id=self.session_id,
            stream_elapsed_seconds=elapsed_seconds,
            viewer_count=0,  # Chat monitor doesn't track viewers
            baseline_viewers=0,
            spike_ratio=0.0  # Not applicable for chat
        )

        print(f"\n{'='*60}")
        print(f"  CHAT SPIKE DETECTED (Moment #{moment_id})")
        print(f"  Type: {trigger_type}")
        print(f"  Velocity: {velocity:.1f} msg/s")
        print(f"  Keywords: {keyword_count}")
        print(f"  Elapsed: {int(elapsed_seconds)}s")
        print(f"{'='*60}\n")

        # Clear windows to avoid duplicate triggers
        self.message_times.clear()
        self.keyword_occurrences.clear()

    def run(self):
        """Main monitoring loop."""
        print(f"\n{'='*60}")
        print(f"Chat Monitor for {self.streamer}")
        print(f"{'='*60}")
        print(f"Velocity threshold: {CHAT_VELOCITY_THRESHOLD} msg/s")
        print(f"Keyword threshold: {KEYWORD_THRESHOLD} mentions")
        print(f"Window: {CHAT_WINDOW_SECONDS}s")
        print(f"Keywords: {', '.join(CLIP_KEYWORDS)}")
        print("-" * 60)

        # Initialize database
        init_db()

        self.running = True
        waiting_for_live = True

        while self.running:
            # Check if stream is live
            is_live = self.get_stream_status()

            if not is_live:
                if not waiting_for_live:
                    # Stream just went offline
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stream went offline.")
                    if self.session_id:
                        end_session(self.session_id)
                        print(f"Session {self.session_id} ended.")
                    self.session_id = None
                    self.stream_start = None
                    self.chatroom_id = None

                    # Close WebSocket
                    if self.ws:
                        self.ws.close()
                        self.ws = None

                waiting_for_live = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {self.streamer} to go live...", end='\r')
                time.sleep(5)
                continue

            # Stream is live
            if waiting_for_live:
                # Stream just went live
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {self.streamer} is LIVE!")
                self.stream_start = time.time()
                self.session_id = start_session(self.streamer)
                print(f"Started session {self.session_id}")

                # Get chatroom ID and connect
                self.chatroom_id = self.get_chatroom_id()
                if self.chatroom_id:
                    if self.connect_websocket():
                        print(f"Chat monitoring active")
                    else:
                        print(f"[WARNING] Failed to connect to chat WebSocket")
                else:
                    print(f"[WARNING] Could not fetch chatroom ID, will retry")

                print("-" * 60)
                waiting_for_live = False

            # Keep connection alive
            time.sleep(2)

    def stop(self):
        """Stop the monitor gracefully."""
        print("\n\nStopping chat monitor...")
        self.running = False

        if self.ws:
            self.ws.close()
            self.ws = None

        if self.session_id:
            end_session(self.session_id)
            print(f"Session {self.session_id} ended.")


def main():
    parser = argparse.ArgumentParser(description="Monitor Kick chat for viral moments")
    parser.add_argument(
        "--streamer", "-s",
        default=DEFAULT_STREAMER,
        help=f"Streamer username (default: {DEFAULT_STREAMER})"
    )
    args = parser.parse_args()

    monitor = ChatMonitor(args.streamer)

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        monitor.run()
    except KeyboardInterrupt:
        monitor.stop()


if __name__ == "__main__":
    main()
