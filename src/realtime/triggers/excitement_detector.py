"""
Excitement Detector for identifying exciting moments in chat messages.

Analyzes chat messages for emotes and phrases that indicate audience excitement,
used as a trigger for clip creation.
"""

from typing import Dict, List
from collections import Counter
from datetime import datetime, timedelta


# Constants for excitement detection
EXCITEMENT_EMOTES = [
    "KEKW", "LUL", "OMEGALUL", "PogChamp", "Pog", "POGGERS",
    "monkaW", "monkaS", "LULW", "PepeLaugh"
]

EXCITEMENT_PHRASES = [
    "NO SHOT", "WHAT", "HOW", "BRO", "DUDE", "HOLY", "WTF",
    "OMG", "LETS GO", "NO WAY", "INSANE", "CLIP IT", "CLIP THAT"
]


class ExcitementDetector:
    """Detects excitement indicators in chat messages."""

    def check_message(self, message: str) -> Dict:
        """
        Analyze a message for excitement indicators.

        Args:
            message: Chat message to analyze

        Returns:
            Dictionary with:
            - has_emote: bool - Whether message contains excitement emote
            - has_phrase: bool - Whether message contains excitement phrase
            - emotes_found: list - All emotes detected
            - phrases_found: list - All phrases detected
            - excitement_score: float - Excitement level 0-1
        """
        if not message:
            return {
                "has_emote": False,
                "has_phrase": False,
                "emotes_found": [],
                "phrases_found": [],
                "excitement_score": 0.0
            }

        message_upper = message.upper()

        # Find emotes (case-insensitive)
        emotes_found = []
        for emote in EXCITEMENT_EMOTES:
            if emote.upper() in message_upper:
                emotes_found.append(emote)

        # Find phrases (case-insensitive)
        phrases_found = []
        for phrase in EXCITEMENT_PHRASES:
            if phrase in message_upper:
                phrases_found.append(phrase)

        has_emote = len(emotes_found) > 0
        has_phrase = len(phrases_found) > 0

        # Calculate excitement score (0-1)
        excitement_score = self._calculate_score(
            has_emote,
            has_phrase,
            len(emotes_found),
            len(phrases_found)
        )

        return {
            "has_emote": has_emote,
            "has_phrase": has_phrase,
            "emotes_found": emotes_found,
            "phrases_found": phrases_found,
            "excitement_score": excitement_score
        }

    def detect_emote_flood(self, messages: List[Dict], window_seconds: int = 5) -> bool:
        """
        Detect if same emote appears 5+ times within a time window.

        Args:
            messages: List of message dicts with 'text' and optional 'timestamp'
            window_seconds: Time window in seconds to check (default: 5)

        Returns:
            True if emote flood detected, False otherwise
        """
        if not messages or len(messages) < 5:
            return False

        # Get the most recent message timestamp as reference
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        # Collect all emotes in the time window
        emote_count = Counter()

        for msg_data in messages:
            msg_text = msg_data.get("text", "") if isinstance(msg_data, dict) else msg_data

            # Check timestamp if provided
            if isinstance(msg_data, dict) and "timestamp" in msg_data:
                msg_time = msg_data["timestamp"]
                if isinstance(msg_time, str):
                    try:
                        msg_time = datetime.fromisoformat(msg_time)
                    except (ValueError, TypeError):
                        msg_time = now
                elif not isinstance(msg_time, datetime):
                    msg_time = now

                if msg_time < window_start:
                    continue

            # Find emotes in this message
            msg_upper = msg_text.upper() if msg_text else ""
            for emote in EXCITEMENT_EMOTES:
                if emote.upper() in msg_upper:
                    emote_count[emote.upper()] += 1

        # Check if any emote appears 5+ times
        return any(count >= 5 for count in emote_count.values())

    @staticmethod
    def _calculate_score(has_emote: bool, has_phrase: bool,
                         emote_count: int, phrase_count: int) -> float:
        """
        Calculate excitement score on a 0-1 scale.

        Scoring:
        - Emote present: 0.3 base, +0.1 per additional emote
        - Phrase present: 0.4 base, +0.1 per additional phrase
        - Max score: 1.0
        """
        score = 0.0

        if has_emote:
            score += 0.3 + (min(emote_count - 1, 2) * 0.1)

        if has_phrase:
            score += 0.4 + (min(phrase_count - 1, 2) * 0.1)

        return min(score, 1.0)
