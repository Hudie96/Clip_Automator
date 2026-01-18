"""
Configuration settings for the Clip Automater.
Adjust these values to tune detection sensitivity and clip parameters.
"""

# ===================
# Detection Settings
# ===================
SPIKE_THRESHOLD = 3.0        # Multiplier: viewers > baseline * this = spike
POLL_INTERVAL = 10           # Seconds between API calls
BASELINE_WINDOW = 60         # Seconds to calculate rolling baseline average
COOLDOWN_AFTER_SPIKE = 30    # Seconds to wait before detecting another spike

# ===================
# Clip Settings
# ===================
CLIP_BEFORE = 20             # Seconds to include before the spike (was 30)
CLIP_AFTER = 25              # Seconds to include after the spike (was 30)
CLIP_FORMAT = "mp4"          # Output format
CLIP_COOLDOWN = 60           # Default seconds between clip creation (prevents spam)
MAX_CLIPS_PER_DAY = 50       # Maximum clips per streamer per day
HIGH_PRIORITY_CONFIDENCE = 0.9  # Confidence threshold (used for scoring, not bypass)

# Per-trigger cooldowns (seconds) - more spammy triggers get longer cooldowns
TRIGGER_COOLDOWNS = {
    "chat_velocity": 120,    # 2 minutes - most common trigger
    "keyword": 90,           # 1.5 minutes
    "emote_flood": 90,       # 1.5 minutes
    "viewer_spike": 60,      # 1 minute - more rare and valuable
    "combo": 30,             # 30 seconds - highest quality signal
    "super_combo": 30,
    "hype_moment": 30,
}

# ===================
# Paths
# ===================
DB_PATH = "data/clips.db"
RECORDINGS_DIR = "recordings"
CLIPS_DIR = "clips"
LOGS_DIR = "logs"

# ===================
# Streamer
# ===================
DEFAULT_STREAMER = "clavicular"
KICK_API_BASE = "https://kick.com/api/v2/channels"

# ===================
# Logging
# ===================
LOG_LEVEL = "INFO"           # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True

# ===================
# Chat Monitor Settings
# ===================
# Tuned thresholds for active streams (2025-01):
# - 10.0 msg/s still triggered on moderately active chat
# - Generic keywords like "OMG", "WTF" triggered too easily
CHAT_VELOCITY_THRESHOLD = 15.0   # messages/second to trigger spike (was 10.0)
CHAT_WINDOW_SECONDS = 10         # rolling window for velocity calc
CLIP_KEYWORDS = [
    # High priority - explicit clip requests
    "CLIP IT", "CLIP THAT", "SOMEONE CLIP", "GET THAT CLIP",
    # Medium priority - strong excitement indicators
    "NO SHOT", "INSANE", "HOLY SHIT", "WHAT THE FUCK"
]
KEYWORD_THRESHOLD = 8            # keyword mentions in window to trigger (was 5)
EMOTE_SPAM_THRESHOLD = 15        # same emote count to trigger (was 10)

# ===================
# Recorder Settings
# ===================
RECORDER_POLL_INTERVAL = 60      # seconds between "is live?" checks
RECORDER_HEALTH_INTERVAL = 60    # seconds between file size checks
MIN_GROWTH_RATE_MB = 1.0         # minimum MB/min to consider healthy

# ===================
# WebSocket Settings
# ===================
PUSHER_WS_URL = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?protocol=7&client=js&version=8.4.0-rc2&flash=false"
WS_RECONNECT_DELAY = 5           # seconds to wait before reconnecting
WS_MAX_RECONNECT_ATTEMPTS = 10   # max reconnect attempts before giving up

# ===================
# Real-Time Segment Settings
# ===================
SEGMENT_DURATION = 10            # Seconds per segment file
SEGMENTS_TO_KEEP = 12            # Rolling buffer size (12 * 10s = 2 minutes)
SEGMENTS_DIR = "segments"        # Temporary segment storage

# ===================
# Smart Trigger Settings
# ===================
DYNAMIC_THRESHOLD_ENABLED = True
BASELINE_WINDOW_MINUTES = 5
COMBO_WINDOW_SECONDS = 10
EXCITEMENT_EMOTES = ["KEKW", "LUL", "OMEGALUL", "PogChamp", "Pog", "POGGERS", "monkaW", "monkaS"]
EXCITEMENT_PHRASES = ["NO SHOT", "WHAT", "HOW", "BRO", "DUDE", "HOLY", "WTF", "OMG", "LETS GO", "NO WAY", "INSANE"]
