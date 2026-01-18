# 📋 Feature Plan: Parallel Coding Agents with Chat Monitor

## Goal
Create parallel coding agent prompts for: (1) Chat Monitor, (2) Improved Recorder, with explicit token optimization and AI reduction strategies.

---

## Part 1: Chat Monitor Agent

### What It Does
Monitors Kick.com chat via WebSocket for "viral moment" signals:
- High message velocity (messages per second)
- Specific phrases ("CLIP THAT", "LMAO", "NO WAY")
- Emote spam detection
- Subscriber/donation alerts

### Technical Approach

**Option A: Use `kickpython` library (Recommended)**
```python
pip install kickpython
```
- Handles WebSocket connection to Pusher
- Provides message handler callbacks
- Automatic reconnection

**Option B: Raw WebSocket (No dependency)**
```python
# Pusher WebSocket endpoint
wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?protocol=7&client=js&version=8.4.0-rc2&flash=false
```
- More control, fewer dependencies
- Need to handle Pusher protocol manually

### New File to Create

`src/monitor/chat_monitor.py`

```
Purpose: Monitor chat velocity and keywords
Inputs: Streamer username
Outputs: Logs moments to SQLite when chat spikes detected
Signals:
  - messages_per_second > 5 → potential moment
  - "CLIP" keyword count > 3 in 10 seconds → definite moment
  - Emote spam (same emote 10+ times in 5 seconds) → potential moment
```

### Database Changes

Add to `moments` table:
```sql
trigger_type TEXT  -- 'viewer_spike', 'chat_velocity', 'keyword', 'emote_spam'
trigger_data TEXT  -- JSON with details (e.g., {"keyword": "CLIP THAT", "count": 5})
```

### Agent Prompt for Chat Monitor

```markdown
# Chat Monitor Agent - Coding Task

## Your Goal
Create `src/monitor/chat_monitor.py` that monitors Kick chat for viral moments.

## Files to Reference
- `src/monitor/realtime_monitor.py` - Follow this pattern for structure
- `src/db/schema.py` - Use these DB functions
- `config/settings.py` - Add new settings here

## Requirements

1. Connect to Kick chat via WebSocket (use kickpython or raw Pusher)
2. Track messages per second (rolling 10-second window)
3. Detect keywords: "CLIP", "CLIP THAT", "NO WAY", "LMAO", "OMG"
4. Log to SQLite when thresholds exceeded
5. Handle disconnections gracefully

## Settings to Add (config/settings.py)
```python
# Chat Monitor Settings
CHAT_VELOCITY_THRESHOLD = 5      # messages/second to trigger
CHAT_WINDOW_SECONDS = 10         # rolling window size
CLIP_KEYWORDS = ["CLIP", "CLIP THAT", "NO WAY", "INSANE"]
KEYWORD_THRESHOLD = 3            # keyword count in window to trigger
```

## Code Structure
```python
class ChatMonitor:
    def __init__(self, streamer: str)
    async def connect(self)
    async def on_message(self, message: dict)
    def calculate_velocity(self) -> float
    def check_keywords(self, content: str) -> bool
    def log_moment(self, trigger_type: str, data: dict)
    async def run(self)
    def stop(self)
```

## Output Format
```
[15:30:45] Connected to clavicular chat
[15:30:46] Chat: 2.3 msg/s | Keywords: 0
[15:31:02] Chat: 8.7 msg/s | Keywords: 5 ← SPIKE
============================================================
  CHAT SPIKE at 1h 23m 45s
  Velocity: 8.7 msg/s | Keywords: CLIP (5x)
============================================================
```

## Do NOT
- Use excessive logging (only log spikes)
- Store full message content (privacy)
- Block on database writes (use async or queue)
```

---

## Part 2: Improved Recorder Agent

### What It Does
Enhanced recording with:
- Auto-start when stream goes live
- Filename includes session ID for correlation
- Health monitoring (file size growing?)

### Agent Prompt for Recorder

```markdown
# Recorder Agent - Coding Task

## Your Goal
Create `src/recorder/stream_recorder.py` that wraps Streamlink with auto-start.

## Files to Reference
- `src/monitor/realtime_monitor.py` - See how it checks if stream is live
- `config/settings.py` - Use KICK_API_BASE

## Requirements

1. Poll API until stream goes live
2. Start Streamlink subprocess
3. Monitor that file size is growing (recording working)
4. Update session in database with recording path
5. Handle stream going offline mid-recording

## Code Structure
```python
class StreamRecorder:
    def __init__(self, streamer: str, session_id: int = None)
    def is_stream_live(self) -> bool
    def start_recording(self) -> subprocess.Popen
    def monitor_recording(self, process: subprocess.Popen)
    def run(self)
    def stop(self)
```

## Streamlink Command
```bash
streamlink https://kick.com/{streamer} best \
  -o "recordings/{streamer}_{session_id}_{timestamp}.mp4" \
  --retry-streams 30 \
  --retry-max 5
```

## Output Format
```
[15:30:00] Waiting for clavicular to go live...
[15:32:15] Stream is LIVE! Starting recording...
[15:32:16] Recording to: recordings/clavicular_s005_20260117_153216.mp4
[15:33:00] Recording health: 45.2 MB (+12.3 MB/min)
```

## Do NOT
- Re-encode video (use -c copy in FFmpeg, default in Streamlink)
- Store in memory (stream directly to disk)
- Ignore errors (log and attempt recovery)
```

---

## Part 3: Token Usage Mitigation Strategy

### How We're Reducing Token Usage

| Strategy | Implementation | Savings |
|----------|----------------|---------|
| **Focused prompts** | Each agent gets ONLY relevant code context | ~60% |
| **No full file dumps** | Reference files by path, not content | ~40% |
| **Structured output** | Clear format reduces back-and-forth | ~30% |
| **Single responsibility** | One agent = one file = focused context | ~50% |

### Token Budget Per Agent

| Agent | Input Context | Expected Output | Total |
|-------|---------------|-----------------|-------|
| Chat Monitor | ~2K tokens (prompt + patterns) | ~3K tokens (code) | ~5K |
| Recorder | ~1.5K tokens (prompt + patterns) | ~2K tokens (code) | ~3.5K |
| Config updates | ~500 tokens | ~500 tokens | ~1K |

**Total estimated: ~9.5K tokens** vs. single agent doing all (~25K tokens)

### Prompt Optimization Techniques

1. **Reference, don't repeat**
   ```
   # BAD (wastes tokens)
   "Here's the full realtime_monitor.py: [500 lines]"

   # GOOD (saves tokens)
   "Follow the pattern in src/monitor/realtime_monitor.py"
   ```

2. **Explicit constraints**
   ```
   # BAD (agent explores unnecessarily)
   "Create a chat monitor"

   # GOOD (focused scope)
   "Create src/monitor/chat_monitor.py with exactly these methods: __init__, connect, on_message, run, stop"
   ```

3. **Output format specification**
   ```
   # Prevents agent from adding unnecessary comments/docs
   "Output ONLY the Python code. No explanations. No markdown."
   ```

---

## Part 4: Reducing AI Dependency

### Where AI Is Currently Used

| Task | AI Role | Can Automate? |
|------|---------|---------------|
| Writing new code | Essential | No |
| Debugging | Helpful | Partially |
| Running commands | Unnecessary | Yes (scripts) |
| Monitoring output | Unnecessary | Yes (scripts) |

### Strategies to Reduce AI Usage

#### 1. **One-Time Code Generation → Permanent Scripts**
```
Current: Ask AI each time to run monitor
Future: Run `python start_session.py` yourself
```

**Create a launcher script:**
```python
# start_session.py - No AI needed after creation
import subprocess
import sys

# Starts all 3 processes in parallel
processes = [
    subprocess.Popen(["python", "src/monitor/realtime_monitor.py"]),
    subprocess.Popen(["python", "src/monitor/chat_monitor.py"]),
    subprocess.Popen(["streamlink", "https://kick.com/clavicular", "best", "-o", "..."])
]

# Wait for Ctrl+C
try:
    for p in processes:
        p.wait()
except KeyboardInterrupt:
    for p in processes:
        p.terminate()
```

#### 2. **Configuration Files Instead of Prompts**
```
Current: "Set spike threshold to 4x"
Future: Edit config/settings.py yourself
```

#### 3. **Scheduled/Triggered Execution**
```
Current: Ask AI to run clipper when stream ends
Future: Cron job or file watcher triggers automatically
```

**Auto-clipper on stream end:**
```python
# In realtime_monitor.py, when stream ends:
if stream_ended:
    subprocess.run(["python", "src/clip/create_clips.py", "--session", str(session_id)])
```

#### 4. **CLI Tool Instead of Conversation**
```
Current: "Create a clip from 1:23:45 to 1:24:45"
Future: python clip.py --start 1:23:45 --duration 60
```

#### 5. **Dashboard/UI (Future)**
```
Current: Ask AI for status
Future: Web dashboard showing real-time stats
```

### AI Usage Reduction Roadmap

| Phase | AI Usage | Human Workflow |
|-------|----------|----------------|
| **Now** | High - AI runs everything | Copy-paste commands |
| **Phase 1** | Medium - AI writes code | User runs scripts |
| **Phase 2** | Low - AI debugs/improves | User configures & runs |
| **Phase 3** | Minimal - AI for new features only | Fully automated pipeline |

### Specific Automation Opportunities

1. **Auto-start on stream live**
   - Script polls API every 60s
   - When live detected → start all processes
   - No AI needed

2. **Auto-clip on stream end**
   - Monitor detects stream offline
   - Automatically runs clipper
   - No AI needed

3. **Auto-upload clips** (future)
   - Watch `clips/` folder
   - Upload to YouTube/TikTok
   - No AI needed

4. **Alerting**
   - Send Discord/SMS when clip created
   - No AI needed

---

## Part 5: Parallel Agent Execution Plan

### Agent Assignment

```
┌─────────────────────────────────────────────────────────────┐
│                   PARALLEL CODE GENERATION                  │
└─────────────────────────────────────────────────────────────┘

   AGENT A                    AGENT B                    AGENT C
   (Chat Monitor)             (Recorder)                 (Config)
        │                          │                          │
        ▼                          ▼                          ▼
   chat_monitor.py           stream_recorder.py          settings.py
        │                          │                          │
        └──────────────────────────┴──────────────────────────┘
                                   │
                                   ▼
                            INTEGRATION TEST
                          (Human or AI verify)
```

### Prompt for Agent A: Chat Monitor
*(See Part 1 above - full prompt ready)*

### Prompt for Agent B: Recorder
*(See Part 2 above - full prompt ready)*

### Prompt for Agent C: Config Updates

```markdown
# Config Agent - Coding Task

## Your Goal
Update `config/settings.py` with new settings for chat monitor and recorder.

## Add These Settings

```python
# ===================
# Chat Monitor Settings
# ===================
CHAT_VELOCITY_THRESHOLD = 5.0    # messages/second to trigger spike
CHAT_WINDOW_SECONDS = 10         # rolling window for velocity calc
CLIP_KEYWORDS = ["CLIP", "CLIP THAT", "NO WAY", "INSANE", "OMG", "WTF"]
KEYWORD_THRESHOLD = 3            # keyword mentions in window to trigger
EMOTE_SPAM_THRESHOLD = 10        # same emote count to trigger

# ===================
# Recorder Settings
# ===================
RECORDER_POLL_INTERVAL = 60      # seconds between "is live?" checks
RECORDER_HEALTH_INTERVAL = 60    # seconds between file size checks
MIN_GROWTH_RATE_MB = 1.0         # minimum MB/min to consider healthy
```

## Do NOT
- Remove existing settings
- Change existing values
- Add comments beyond what's shown
```

---

## Files Summary

| File | Status | Agent |
|------|--------|-------|
| `src/monitor/chat_monitor.py` | Create | Agent A |
| `src/recorder/stream_recorder.py` | Create | Agent B |
| `config/settings.py` | Modify | Agent C |
| `src/db/schema.py` | Modify (add trigger columns) | Agent A or separate |

---

## Dependencies

- [ ] `kickpython` or `websockets` for chat monitoring
- [ ] Existing: `streamlink`, `ffmpeg`, `requests`

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Pusher WebSocket URL changes | Document how to find new URL in network tab |
| Chat rate limiting | Add exponential backoff on reconnect |
| Agents produce conflicting code | Each agent works on separate files |
| Token usage spikes | Strict prompt boundaries, no file dumps |

---

## Open Questions

1. **Chat library preference?** `kickpython` (easier) vs raw WebSocket (no deps)?
2. **Trigger priority?** If both viewer spike AND chat spike, log as one or two moments?
3. **Auto-clipper?** Should clipper run automatically when stream ends?

---

## Sources

- [kickpython on PyPI](https://pypi.org/project/kickpython/)
- [Kick REST API Documentation](https://github.com/mattseabrook/KICK.com-Streaming-REST-API)
- [kick-chat-wrapper (Go reference)](https://github.com/SongoMen/kick-chat-wrapper)
- [KickLib (C# reference)](https://github.com/Bukk94/KickLib)

---

*Plan created: 2026-01-17*
*Ready for parallel agent execution*
