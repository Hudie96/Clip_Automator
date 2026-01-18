"""
Chat Analyzer - Analyzes VOD chat replay to detect highlight moments.

This is a premium feature that uses chat velocity, emote floods,
and keyword detection to find interesting moments in VODs.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

# Add parent path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import (
    CHAT_VELOCITY_THRESHOLD,
    CLIP_KEYWORDS,
    KEYWORD_THRESHOLD,
    EMOTE_SPAM_THRESHOLD,
    EXCITEMENT_EMOTES,
    EXCITEMENT_PHRASES
)


@dataclass
class HighlightMoment:
    """A detected highlight moment in the VOD."""
    timestamp_seconds: int
    timestamp_display: str
    trigger_type: str
    confidence: float
    data: Dict
    description: str

    def to_dict(self) -> Dict:
        return {
            'timestamp_seconds': self.timestamp_seconds,
            'timestamp_display': self.timestamp_display,
            'trigger_type': self.trigger_type,
            'confidence': self.confidence,
            'data': self.data,
            'description': self.description
        }


class ChatAnalyzer:
    """
    Analyzes VOD chat replay to detect highlight moments.

    Detection methods:
    - Chat velocity spikes (messages per second)
    - Keyword floods (clip requests, excitement)
    - Emote spam (same emote repeated)
    - Combo triggers (multiple signals at once)
    """

    KICK_API_BASE = "https://kick.com/api/v2"

    def __init__(self):
        # Analysis parameters
        self.velocity_threshold = CHAT_VELOCITY_THRESHOLD
        self.keyword_threshold = KEYWORD_THRESHOLD
        self.emote_threshold = EMOTE_SPAM_THRESHOLD
        self.window_seconds = 10  # Analysis window size
        self.min_gap_seconds = 30  # Minimum gap between highlights

        # Keywords and patterns
        self.clip_keywords = [kw.upper() for kw in CLIP_KEYWORDS]
        self.excitement_emotes = EXCITEMENT_EMOTES
        self.excitement_phrases = [p.upper() for p in EXCITEMENT_PHRASES]

    def get_chat_replay(self, vod_id: str) -> List[Dict]:
        """
        Fetch chat replay data for a VOD.

        Note: Kick's API may not provide full chat replay.
        This is a best-effort implementation.

        Args:
            vod_id: The VOD ID

        Returns:
            List of chat messages with timestamps
        """
        # Try the video-specific chat endpoint
        url = f"{self.KICK_API_BASE}/video/{vod_id}/messages"

        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                messages = data.get('data', []) if isinstance(data, dict) else data
                return messages
            else:
                print(f"[chat_analyzer] Chat replay not available (status {response.status_code})")
                return []

        except requests.RequestException as e:
            print(f"[chat_analyzer] Error fetching chat replay: {e}")
            return []

    def _format_timestamp(self, seconds: int) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _calculate_message_offset(self, message: Dict, vod_start_time: datetime) -> int:
        """Calculate the offset in seconds from VOD start for a message."""
        # Try different timestamp fields
        timestamp_str = message.get('created_at') or message.get('timestamp') or message.get('sent_at')

        if not timestamp_str:
            return 0

        try:
            # Parse the timestamp
            if 'T' in str(timestamp_str):
                msg_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                msg_time = datetime.fromtimestamp(float(timestamp_str))

            # Calculate offset from VOD start
            offset = (msg_time - vod_start_time).total_seconds()
            return max(0, int(offset))

        except (ValueError, TypeError):
            return 0

    def analyze_vod(
        self,
        vod_id: str,
        vod_duration: int = 0,
        vod_start_time: Optional[str] = None
    ) -> List[HighlightMoment]:
        """
        Analyze a VOD's chat to detect highlight moments.

        Args:
            vod_id: The VOD ID to analyze
            vod_duration: Duration of the VOD in seconds
            vod_start_time: ISO timestamp when VOD started

        Returns:
            List of detected HighlightMoment objects
        """
        print(f"[chat_analyzer] Analyzing VOD {vod_id}...")

        # Fetch chat replay
        messages = self.get_chat_replay(vod_id)

        if not messages:
            print("[chat_analyzer] No chat messages found - generating simulated analysis")
            # If no chat data available, return simulated highlights based on VOD duration
            return self._generate_simulated_highlights(vod_duration)

        print(f"[chat_analyzer] Processing {len(messages)} messages...")

        # Parse VOD start time
        start_time = None
        if vod_start_time:
            try:
                start_time = datetime.fromisoformat(vod_start_time.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Group messages by time window
        windows = self._group_by_window(messages, start_time)

        # Detect highlights
        highlights = []
        last_highlight_time = -self.min_gap_seconds

        for window_start, window_messages in windows.items():
            # Skip if too close to last highlight
            if window_start - last_highlight_time < self.min_gap_seconds:
                continue

            # Analyze this window
            moment = self._analyze_window(window_start, window_messages)

            if moment:
                highlights.append(moment)
                last_highlight_time = window_start

        print(f"[chat_analyzer] Detected {len(highlights)} highlight moments")
        return highlights

    def _group_by_window(
        self,
        messages: List[Dict],
        vod_start: Optional[datetime]
    ) -> Dict[int, List[Dict]]:
        """Group messages into time windows."""
        windows = defaultdict(list)

        for msg in messages:
            # Get message offset in VOD
            if vod_start:
                offset = self._calculate_message_offset(msg, vod_start)
            else:
                # Try to use relative offset if provided
                offset = msg.get('offset', 0) or msg.get('video_offset', 0)

            # Round to window
            window_start = (offset // self.window_seconds) * self.window_seconds
            windows[window_start].append(msg)

        return dict(sorted(windows.items()))

    def _analyze_window(
        self,
        window_start: int,
        messages: List[Dict]
    ) -> Optional[HighlightMoment]:
        """Analyze a single time window for highlight potential."""
        if not messages:
            return None

        # Calculate metrics
        msg_count = len(messages)
        velocity = msg_count / self.window_seconds

        # Extract message content
        contents = [
            (msg.get('content', '') or msg.get('message', '') or '').upper()
            for msg in messages
        ]

        # Count keywords
        keyword_count = sum(
            1 for content in contents
            if any(kw in content for kw in self.clip_keywords + self.excitement_phrases)
        )

        # Count emotes
        emote_counts = defaultdict(int)
        for content in contents:
            for emote in self.excitement_emotes:
                if emote in content:
                    emote_counts[emote] += 1

        max_emote_count = max(emote_counts.values()) if emote_counts else 0

        # Determine trigger type and confidence
        triggers = []

        if velocity >= self.velocity_threshold:
            triggers.append(('chat_velocity', velocity / self.velocity_threshold))

        if keyword_count >= self.keyword_threshold:
            triggers.append(('keyword', keyword_count / self.keyword_threshold))

        if max_emote_count >= self.emote_threshold:
            triggers.append(('emote_flood', max_emote_count / self.emote_threshold))

        if not triggers:
            return None

        # Calculate overall confidence
        confidence = sum(t[1] for t in triggers) / len(triggers)
        confidence = min(1.0, confidence)

        # Determine primary trigger
        primary_trigger = max(triggers, key=lambda t: t[1])[0]

        # Generate description
        descriptions = {
            'chat_velocity': f"Chat spike ({velocity:.1f} msg/sec)",
            'keyword': f"Keyword activity ({keyword_count} mentions)",
            'emote_flood': f"Emote flood ({max_emote_count} emotes)"
        }

        # Check for combo
        if len(triggers) >= 2:
            primary_trigger = 'combo'
            description = f"Multiple triggers: {', '.join(t[0] for t in triggers)}"
        else:
            description = descriptions[primary_trigger]

        return HighlightMoment(
            timestamp_seconds=window_start,
            timestamp_display=self._format_timestamp(window_start),
            trigger_type=primary_trigger,
            confidence=confidence,
            data={
                'velocity': velocity,
                'keyword_count': keyword_count,
                'emote_count': max_emote_count,
                'message_count': msg_count
            },
            description=description
        )

    def _generate_simulated_highlights(self, duration: int) -> List[HighlightMoment]:
        """
        Generate simulated highlights when chat data is unavailable.

        This creates potential highlight points based on common patterns:
        - Every 15-20 minutes there's likely something interesting
        - Early moments (first 5 min) and ending are often highlight-worthy

        Args:
            duration: VOD duration in seconds

        Returns:
            List of simulated HighlightMoment objects
        """
        if duration <= 0:
            duration = 3600  # Default to 1 hour

        highlights = []

        # Add highlight near the start (intro/first moments)
        if duration > 300:
            highlights.append(HighlightMoment(
                timestamp_seconds=180,
                timestamp_display=self._format_timestamp(180),
                trigger_type='suggested',
                confidence=0.5,
                data={'source': 'pattern_based'},
                description="Stream start - potential intro moment"
            ))

        # Add highlights every ~15 minutes
        interval = 900  # 15 minutes
        current = interval

        while current < duration - 300:  # Stop 5 min before end
            highlights.append(HighlightMoment(
                timestamp_seconds=current,
                timestamp_display=self._format_timestamp(current),
                trigger_type='suggested',
                confidence=0.4,
                data={'source': 'interval_based'},
                description=f"Checkpoint at {self._format_timestamp(current)}"
            ))
            current += interval

        # Add highlight near the end
        if duration > 600:
            end_moment = duration - 300  # 5 minutes before end
            highlights.append(HighlightMoment(
                timestamp_seconds=end_moment,
                timestamp_display=self._format_timestamp(end_moment),
                trigger_type='suggested',
                confidence=0.5,
                data={'source': 'pattern_based'},
                description="Near stream end - potential finale"
            ))

        return highlights


if __name__ == "__main__":
    # Test the chat analyzer
    analyzer = ChatAnalyzer()

    # Test with simulated data
    print("Testing with simulated highlights for 2-hour VOD...")
    highlights = analyzer._generate_simulated_highlights(7200)

    for h in highlights:
        print(f"  [{h.timestamp_display}] {h.trigger_type}: {h.description} (conf: {h.confidence:.2f})")
