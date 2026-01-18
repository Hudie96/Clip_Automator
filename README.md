# Clip Automater

Automated real-time stream clipping for Kick.com. Monitors viewer counts, chat activity, keywords, and emote floods to detect viral moments and create clips instantly.

## Features

| Feature | Description |
|---------|-------------|
| **Real-time Recording** | FFmpeg segments stream into 10-second chunks for instant clipping |
| **Multi-Trigger Detection** | Viewer spikes, chat velocity, keywords, emote floods |
| **Smart Thresholds** | Dynamic baselines adapt to each channel's activity level |
| **Combo Detection** | Multiple triggers = higher confidence = priority clips |
| **Web Dashboard** | Live monitoring, clip review, gaming-inspired dark UI |
| **Multi-Streamer** | Monitor multiple streamers simultaneously |
| **Clip Review System** | Approve/reject clips before they pile up |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- FFmpeg (included in `tools/` or install via package manager)
- Streamlink

### 2. Configure Streamers

Create/edit `config/streamers.json`:
```json
{
  "streamers": ["clavicular", "ninja", "xqc"]
}
```

### 3. Run the Clipper

```bash
# Single streamer
python -m src.realtime.realtime_clipper --streamer clavicular

# All streamers from config
python -m src.realtime.realtime_clipper --multi

# List configured streamers
python -m src.realtime.realtime_clipper --list
```

### 4. Start the Dashboard

```bash
python -m src.web.dashboard --port 5000
```

Open http://127.0.0.1:5000

---

## Configuration

All settings in `config/settings.py`:

### Clip Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `CLIP_BEFORE` | 20s | Seconds of video before trigger |
| `CLIP_AFTER` | 25s | Seconds of video after trigger |
| `CLIP_COOLDOWN` | 60s | Default cooldown between clips |
| `MAX_CLIPS_PER_DAY` | 50 | Per-streamer daily limit |

### Per-Trigger Cooldowns

| Trigger | Cooldown | Rationale |
|---------|----------|-----------|
| `chat_velocity` | 120s | Most common, needs longer cooldown |
| `keyword` | 90s | Moderate frequency |
| `emote_flood` | 90s | Moderate frequency |
| `viewer_spike` | 60s | Rare and valuable |
| `combo` / `super_combo` | 30s | Highest quality signal |

### Trigger Thresholds

| Trigger | Threshold | Description |
|---------|-----------|-------------|
| Chat Velocity | 15 msg/sec | + 2.0 buffer above dynamic baseline |
| Keyword | 8 mentions | In 10-second window |
| Emote Spam | 15 emotes | Same emote count |
| Viewer Spike | 3.0x | Must reach 3x rolling baseline |

### Keywords Monitored

```python
CLIP_KEYWORDS = [
    # High priority - explicit clip requests
    "CLIP IT", "CLIP THAT", "SOMEONE CLIP", "GET THAT CLIP",
    # Medium priority - excitement indicators
    "NO SHOT", "INSANE", "HOLY SHIT", "WHAT THE FUCK"
]
```

---

## Project Structure

```
Clipping automater/
├── config/
│   ├── settings.py              # All configuration values
│   └── streamers.json           # Streamer list to monitor
│
├── src/
│   ├── realtime/
│   │   ├── realtime_clipper.py  # Main entry point
│   │   └── triggers/
│   │       ├── base.py          # TriggerEvent dataclass
│   │       ├── viewer_trigger.py    # Viewer spike detection
│   │       ├── chat_trigger.py      # Chat velocity + keywords + emotes
│   │       ├── combo_trigger.py     # Multi-trigger combos
│   │       ├── dynamic_baseline.py  # Adaptive thresholds
│   │       └── excitement_detector.py # Sentiment analysis
│   │
│   ├── web/
│   │   ├── dashboard.py         # Flask web server
│   │   ├── api.py               # REST API endpoints
│   │   ├── live_stats.py        # WebSocket live updates
│   │   ├── streamer_search.py   # Kick API search for streamers
│   │   └── templates/
│   │       └── dashboard.html   # Gaming-style dark UI (responsive)
│   │
│   ├── db/
│   │   └── schema.py            # SQLite schema + queries
│   │
│   ├── clip/
│   │   ├── create_clips.py      # FFmpeg clip extraction
│   │   └── editor.py            # Trim/edit clips with in/out points
│   │
│   ├── vod/
│   │   ├── __init__.py          # VOD module
│   │   ├── vod_clipper.py       # VOD download and clipping
│   │   └── chat_analyzer.py     # Chat replay analysis for highlights
│   │
│   ├── monitor/
│   │   ├── chat_monitor.py      # Pusher WebSocket chat
│   │   └── realtime_monitor.py  # Viewer count polling
│   │
│   ├── recorder/
│   │   └── stream_recorder.py   # HLS stream recording
│   │
│   ├── upload/
│   │   ├── manager.py           # Upload orchestration
│   │   ├── youtube.py           # YouTube API upload
│   │   └── tiktok.py            # TikTok upload (placeholder)
│   │
│   └── utils/
│       ├── cleanup.py           # Segment cleanup
│       ├── thumbnails.py        # Thumbnail generation
│       └── timestamp.py         # Time utilities
│
├── clips/                       # Output clips (per-streamer subdirs)
├── segments/                    # Temporary 10s recording segments
├── data/                        # SQLite database
├── logs/                        # Application logs
├── tools/                       # FFmpeg binaries
└── docs/
    └── ARCHITECTURE.md          # Future SaaS architecture
```

---

## Triggers Explained

### 1. Viewer Spike (`viewer_trigger.py`)

```
Polls Kick API → Maintains 60s rolling baseline → Fires when viewers >= 3x baseline
```

- Polls every 10 seconds
- Rare but high-value signal
- 60s cooldown

### 2. Chat Velocity (`chat_trigger.py`)

```
WebSocket chat → Track messages/second → Dynamic threshold adapts → Fire when velocity exceeds
```

- Connects via Pusher WebSocket
- Dynamic baseline prevents false positives on active channels
- Requires velocity > threshold + 2.0 buffer
- 120s cooldown (most common trigger)

### 3. Keywords (`chat_trigger.py`)

```
Monitor chat → Count keyword matches in 10s window → Fire when count >= 8
```

- Focused on clip-worthy phrases
- Ignores generic words like "OMG", "WTF" (too common)
- 90s cooldown

### 4. Emote Flood (`chat_trigger.py`)

```
Track emotes → Detect spam of same emote → Fire when count >= 15
```

- Indicates chat reacting to something
- 90s cooldown

### 5. Combos (`combo_trigger.py`)

```
Track recent triggers → Detect multiple within 10s → Fire combo with higher confidence
```

| Combo Type | Triggers | Confidence |
|------------|----------|------------|
| `chat_combo` | 2 chat triggers | 0.7 |
| `hype_moment` | Chat + Emotes | 0.8 |
| `clip_worthy` | Chat + Viewer | 0.85 |
| `super_combo` | 3+ triggers | 0.95 |

Combos bypass per-trigger cooldowns due to high confidence.

---

## Rate Limiting

Prevents clip spam with multiple layers:

| Layer | Setting | Effect |
|-------|---------|--------|
| Per-Trigger Cooldown | 30-120s | Each trigger type has own cooldown |
| Daily Limit | 50 clips | Hard cap per streamer per day |
| Dynamic Baseline | +2.0 buffer | Velocity must clearly exceed threshold |
| Priority Bypass | Combos only | Only high-confidence combos skip cooldown |

---

## API Endpoints

### Clip Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clips/<filename>` | DELETE | Delete a clip |
| `/api/clips/<filename>` | PATCH | Rename a clip |
| `/api/clips/<filename>/favorite` | POST | Toggle favorite |
| `/api/clips/<filename>/metadata` | GET | Get clip metadata (duration, etc.) |
| `/api/favorites` | GET | List favorites |

### Clip Review

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/review/pending` | GET | Get clips pending review |
| `/api/review/stats` | GET | Get review statistics |
| `/api/review/<id>/approve` | POST | Approve a clip |
| `/api/review/<id>/reject` | POST | Reject a clip |
| `/api/review/<id>` | DELETE | Delete immediately |
| `/api/review/bulk` | POST | Bulk approve/reject |

### Clip Editor

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clips/trim` | POST | Trim a clip with in/out points |
| `/api/clips/trim/status/<job_id>` | GET | Check trim job status |

### Streamer Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/streamers/search` | GET | Search Kick for streamers (`?q=query`) |
| `/api/streamers/add` | POST | Add streamer to monitoring list |
| `/api/streamers/<name>` | DELETE | Remove streamer from monitoring |
| `/api/streamers/list` | GET | List all monitored streamers |

### VOD Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vods/list/<streamer>` | GET | List VODs for a streamer |
| `/api/vods/clip` | POST | Create clip from VOD |
| `/api/vods/clip/status/<job_id>` | GET | Check VOD clip job status |
| `/api/vods/analyze/<vod_id>` | POST | Analyze VOD chat for highlights |

---

## Dashboard Features

- **Live Stream Preview** - Embedded Kick player (collapsible)
- **Real-time Stats** - Viewers, chat velocity, triggers via WebSocket
- **Clip Grid** - Thumbnails with hover-to-preview video
- **Review Tab** - Approve/reject pending clips
- **Fullscreen Slide Deck Review** - Review clips one-by-one with keyboard shortcuts
- **Streamer Search Tab** - Search Kick for live streamers, add to monitoring
- **VOD Clipper Tab** - Clip from past broadcasts (manual + auto-detect)
- **Clip Editor** - Trim clips with in/out points, preview, and export
- **Responsive Layout** - Dashboard fits on screen, no scrolling required
- **Filtering** - By streamer, trigger type, favorites
- **Dark Gaming UI** - Purple/cyan accent colors

---

## Keyboard Shortcuts

### Review Slideshow

| Key | Action |
|-----|--------|
| `←` `→` | Navigate between clips |
| `Space` | Play/pause video |
| `A` | Approve clip |
| `R` | Reject clip |
| `F` | Toggle favorite |
| `D` | Delete clip |
| `Esc` | Close slideshow |

### Clip Editor

| Key | Action |
|-----|--------|
| `I` | Set in-point (trim start) |
| `O` | Set out-point (trim end) |
| `P` | Preview trim |
| `Space` | Play/pause |
| `←` `→` | Seek 5 seconds |
| `Esc` | Close editor |

---

## VOD Clipper

Create clips from past broadcasts (VODs) on Kick.

### Manual Clipping

1. Go to the **VODs** tab in the dashboard
2. Select a streamer and browse their past broadcasts
3. Enter a timestamp and duration to create a clip

### Auto-Detect (Chat Analysis)

Uses chat replay data to find exciting moments in VODs:

1. Click "Analyze VOD" on any past broadcast
2. The system scans chat replay for spikes in activity
3. Suggested clip moments appear with timestamps
4. One-click to create clips from suggestions

**Note:** Auto-detect uses credits (1 credit per VOD analyzed)

---

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `sessions` | Track each monitoring session |
| `moments` | Detected viral moments |
| `clips` | Clip review status (pending/approved/rejected) |

### Clip Status Flow

```
Created → pending → approved (keep)
                  → rejected (delete later)
```

---

## Future Plans

See `docs/ARCHITECTURE.md` for multi-user SaaS architecture:

- Cloud storage (Backblaze B2)
- User authentication
- Per-user streamer configs
- Auto-upload to YouTube/TikTok
- Pricing tiers

---

## Troubleshooting

### Clipper not detecting triggers

1. Check if stream is live: `python -m src.realtime.realtime_clipper --list`
2. Lower thresholds in `config/settings.py`
3. Check logs in `logs/` directory

### Too many clips

1. Increase `CLIP_COOLDOWN` or per-trigger cooldowns
2. Increase `CHAT_VELOCITY_THRESHOLD`
3. Increase `MINIMUM_SPIKE_BUFFER` in `dynamic_baseline.py`

### FFmpeg errors

1. Ensure FFmpeg is in `tools/` or system PATH
2. Check stream URL is valid
3. Review FFmpeg output in clipper logs

---

## License

MIT
