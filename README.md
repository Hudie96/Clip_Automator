# Clip Automater

Automated stream clipping for Kick.com streamers. Monitors viewer counts, chat activity, and keywords to detect viral moments and create clips in real-time.

## Features

- **Real-time Stream Recording** - Records in 10-second segments for instant clipping
- **Multi-Trigger Detection** - Viewer spikes, chat velocity, keywords, emote floods
- **Smart Triggers** - Dynamic thresholds per channel, combo detection
- **Web Dashboard** - Live monitoring, clip management, gaming-inspired UI
- **Multi-Streamer Support** - Monitor multiple streamers simultaneously

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Streamers

Edit `config/streamers.json`:
```json
{
  "streamers": ["clavicular", "ninja", "xqc"]
}
```

### 3. Run the Clipper

```bash
# Single streamer (first from config)
python src/realtime/realtime_clipper.py

# Specific streamer
python src/realtime/realtime_clipper.py -s ninja

# All streamers from config
python src/realtime/realtime_clipper.py --multi
```

### 4. Start the Dashboard

```bash
python src/web/dashboard.py --port 5000
```

Open http://127.0.0.1:5000 in your browser.

## Configuration

All settings are in `config/settings.py`:

### Clip Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `CLIP_BEFORE` | 20s | Seconds before trigger |
| `CLIP_AFTER` | 25s | Seconds after trigger |
| `CLIP_COOLDOWN` | 60s | Minimum seconds between clips |
| `MAX_CLIPS_PER_DAY` | 50 | Maximum clips per streamer per day |

### Trigger Thresholds
| Trigger | Threshold | Description |
|---------|-----------|-------------|
| Chat Velocity | 15 msg/sec | Messages per second to trigger |
| Keyword | 8 mentions | Keyword mentions in 10s window |
| Emote Spam | 15 emotes | Same emote count to trigger |
| Viewer Spike | 3.0x | Viewers must reach 3x baseline |

### Keywords Monitored
```python
CLIP_KEYWORDS = [
    "CLIP IT", "CLIP THAT", "SOMEONE CLIP", "GET THAT CLIP",
    "NO SHOT", "INSANE", "HOLY SHIT", "WHAT THE FUCK"
]
```

## Project Structure

```
Clipping automater/
├── config/
│   ├── settings.py          # All configuration
│   └── streamers.json       # Streamer list
├── src/
│   ├── realtime/
│   │   ├── realtime_clipper.py   # Main clipper
│   │   └── triggers/             # Trigger classes
│   │       ├── viewer_trigger.py
│   │       ├── chat_trigger.py
│   │       ├── combo_trigger.py
│   │       ├── dynamic_baseline.py
│   │       └── excitement_detector.py
│   ├── web/
│   │   ├── dashboard.py      # Flask web server
│   │   ├── api.py            # REST API endpoints
│   │   └── templates/        # HTML templates
│   └── utils/
│       ├── cleanup.py        # Segment cleanup
│       └── thumbnails.py     # Thumbnail generation
├── clips/                    # Output clips (per-streamer subdirs)
├── segments/                 # Temporary recording segments
├── tools/                    # FFmpeg binaries
└── data/                     # SQLite database
```

## Triggers Explained

### Viewer Spike
- Polls Kick API every 10 seconds
- Maintains 60-second rolling baseline
- Fires when viewers >= 3x baseline

### Chat Velocity
- Connects via Pusher WebSocket
- Tracks messages per second
- Dynamic threshold adapts to channel activity

### Keywords
- Monitors chat for specific phrases
- Requires 8+ mentions in 10-second window
- Focused on clip-worthy phrases

### Emote Flood
- Detects spam of same emote
- Requires 15+ of same emote in window

### Combos
- Detects multiple triggers within 10 seconds
- Higher confidence = bypasses cooldown
- Types: `chat_combo`, `hype_moment`, `clip_worthy`, `super_combo`

## Rate Limiting

To prevent clip spam:

1. **Cooldown**: 60 seconds between clips (configurable)
2. **Daily Limit**: 50 clips per streamer per day
3. **Priority Bypass**: Combos and viewer spikes can bypass cooldown

## Dashboard Features

- **Live Stream Preview** - Embedded Kick player
- **Real-time Stats** - Viewers, chat velocity, triggers
- **Clip Management** - Delete, rename, favorite clips
- **Filtering** - By streamer, trigger type, favorites

## Requirements

- Python 3.8+
- FFmpeg (included in `tools/`)
- Streamlink
- Flask + Flask-SocketIO

## License

MIT
