"""
Real-time stream monitor for detecting viral moments.

Usage:
    python src/monitor/realtime_monitor.py --streamer clavicular

This script:
1. Polls the Kick API for viewer count
2. Detects viewer spikes (3x baseline by default)
3. Logs detected moments to SQLite for later clipping
"""

import argparse
import cloudscraper
import time
import signal
import sys
import os
from datetime import datetime
from collections import deque

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import (
    SPIKE_THRESHOLD,
    POLL_INTERVAL,
    BASELINE_WINDOW,
    COOLDOWN_AFTER_SPIKE,
    KICK_API_BASE,
    DEFAULT_STREAMER,
    LOG_LEVEL
)
from src.db.schema import init_db, start_session, end_session, log_moment
from src.utils.timestamp import parse_stream_start_time, calculate_stream_elapsed, format_duration


class StreamMonitor:
    def __init__(self, streamer: str):
        self.streamer = streamer
        self.api_url = f"{KICK_API_BASE}/{streamer}"
        self.session_id = None
        self.stream_start = None
        self.running = False

        # Rolling window for baseline calculation
        self.viewer_history = deque(maxlen=int(BASELINE_WINDOW / POLL_INTERVAL))
        self.last_spike_time = 0

        # Use cloudscraper to bypass Cloudflare protection
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

    def get_stream_data(self) -> dict:
        """Fetch current stream data from Kick API."""
        try:
            response = self.scraper.get(self.api_url, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[ERROR] API request failed: {e}")
            return None

    def calculate_baseline(self) -> float:
        """Calculate rolling average of viewer count."""
        if not self.viewer_history:
            return 0
        return sum(self.viewer_history) / len(self.viewer_history)

    def check_for_spike(self, current_viewers: int, baseline: float) -> tuple:
        """
        Check if current viewers indicate a spike.
        Returns (is_spike, spike_ratio)
        """
        if baseline <= 0:
            return False, 0

        ratio = current_viewers / baseline

        # Check cooldown
        elapsed_since_spike = time.time() - self.last_spike_time
        if elapsed_since_spike < COOLDOWN_AFTER_SPIKE:
            return False, ratio

        if ratio >= SPIKE_THRESHOLD:
            return True, ratio

        return False, ratio

    def log_status(self, viewers: int, baseline: float, ratio: float, is_spike: bool = False):
        """Print current status to console."""
        elapsed = calculate_stream_elapsed(self.stream_start)
        elapsed_str = format_duration(elapsed)

        if is_spike:
            print(f"\n{'='*60}")
            print(f"  SPIKE DETECTED at {elapsed_str}")
            print(f"  Viewers: {viewers:,} ({ratio:.1f}x baseline)")
            print(f"{'='*60}\n")
        else:
            status = f"[{datetime.now().strftime('%H:%M:%S')}] "
            status += f"Stream: {elapsed_str} | "
            status += f"Viewers: {viewers:,} | "
            status += f"Baseline: {baseline:.0f} | "
            status += f"Ratio: {ratio:.1f}x"
            print(status)

    def run(self):
        """Main monitoring loop."""
        print(f"\nMonitoring {self.streamer}'s stream...")
        print(f"Spike threshold: {SPIKE_THRESHOLD}x baseline")
        print(f"Poll interval: {POLL_INTERVAL}s")
        print("-" * 50)

        # Initialize database
        init_db()

        self.running = True
        waiting_for_live = True

        while self.running:
            data = self.get_stream_data()

            if not data:
                time.sleep(POLL_INTERVAL)
                continue

            # Check if stream is live
            livestream = data.get('livestream')
            is_live = livestream and livestream.get('is_live', False)

            if not is_live:
                if not waiting_for_live:
                    # Stream just went offline
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Stream went offline.")
                    if self.session_id:
                        end_session(self.session_id)
                        print(f"Session {self.session_id} ended.")
                    self.session_id = None
                    self.stream_start = None
                    self.viewer_history.clear()

                waiting_for_live = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for {self.streamer} to go live...", end='\r')
                time.sleep(POLL_INTERVAL)
                continue

            # Stream is live
            if waiting_for_live:
                # Stream just went live
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {self.streamer} is LIVE!")
                self.stream_start = parse_stream_start_time(data)
                self.session_id = start_session(self.streamer)
                print(f"Started session {self.session_id}")
                print("-" * 50)
                waiting_for_live = False

            # Get viewer count
            viewers = livestream.get('viewer_count', 0)
            self.viewer_history.append(viewers)

            # Calculate baseline and check for spike
            baseline = self.calculate_baseline()
            is_spike, ratio = self.check_for_spike(viewers, baseline)

            # Log status
            self.log_status(viewers, baseline, ratio, is_spike)

            # If spike detected, log to database
            if is_spike:
                elapsed_seconds = calculate_stream_elapsed(self.stream_start)
                moment_id = log_moment(
                    session_id=self.session_id,
                    stream_elapsed_seconds=elapsed_seconds,
                    viewer_count=viewers,
                    baseline_viewers=int(baseline),
                    spike_ratio=ratio
                )
                print(f"Logged moment #{moment_id} at {format_duration(elapsed_seconds)}")
                self.last_spike_time = time.time()

                # Update baseline to prevent repeated triggers
                # Fill history with current value
                for _ in range(len(self.viewer_history)):
                    self.viewer_history.append(viewers)

            time.sleep(POLL_INTERVAL)

    def stop(self):
        """Stop the monitor gracefully."""
        print("\n\nStopping monitor...")
        self.running = False

        if self.session_id:
            end_session(self.session_id)
            print(f"Session {self.session_id} ended.")


def main():
    parser = argparse.ArgumentParser(description="Monitor Kick stream for viral moments")
    parser.add_argument(
        "--streamer", "-s",
        default=DEFAULT_STREAMER,
        help=f"Streamer username (default: {DEFAULT_STREAMER})"
    )
    args = parser.parse_args()

    monitor = StreamMonitor(args.streamer)

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
