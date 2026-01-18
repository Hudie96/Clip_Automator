# 📋 Feature Plan: Parallel Agent Architecture for Stream Clipping

## Goal
Create detailed prompts for multiple AI agents that run in parallel to monitor, record, and clip streams.

## Current State

Your codebase already has:
- `realtime_monitor.py` - Monitors viewer spikes via Kick API
- `create_clips.py` - Creates FFmpeg clips from timestamps
- `schema.py` - SQLite coordination database
- `timestamp.py` - Time conversion utilities

## Scope
- ✅ In scope: Agent prompts for parallel execution
- ✅ In scope: Inter-agent communication strategy
- ✅ In scope: Error handling instructions
- ❌ Out of scope: Actually modifying existing code (planning only)

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL AGENT ARCHITECTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AGENT 1        │    │  AGENT 2        │    │  AGENT 3        │
│  MONITOR        │    │  RECORDER       │    │  CLIPPER        │
│                 │    │                 │    │                 │
│  Kick API       │    │  Streamlink     │    │  FFmpeg         │
│  Spike detect   │───▶│  Continuous     │───▶│  Process queue  │
│  SQLite write   │    │  recording      │    │  SQLite read    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                     │                     │
         └──────────┬──────────┴──────────┬──────────┘
                    ▼                     ▼
            ┌─────────────────┐   ┌─────────────────┐
            │  SQLite DB      │   │  File System    │
            │  (coordination) │   │  recordings/    │
            │  data/clips.db  │   │  clips/         │
            └─────────────────┘   └─────────────────┘
```

---

## AGENT 1: Stream Monitor Agent

### Purpose
Poll Kick API and detect viewer spikes. Write detected moments to SQLite.

### Full Prompt for AI Agent

```markdown
# Stream Monitor Agent

## Your Role
You are the Stream Monitor Agent. Your job is to monitor a Kick.com stream for
"viral moments" by detecting viewer count spikes.

## Configuration
- Streamer: `clavicular` (default, configurable)
- Spike threshold: 3x baseline (rolling average)
- Poll interval: 10 seconds
- Cooldown: 30 seconds between spike detections

## Execution Steps

### Step 1: Initialize
```bash
cd "E:\Coding Projects\Clipping automater"
python -c "from src.db.schema import init_db; init_db()"
```

### Step 2: Run Monitor
```bash
python src/monitor/realtime_monitor.py --streamer clavicular
```

### Step 3: Monitor Output
Watch for lines like:
```
==============================================================
  SPIKE DETECTED at 1h 23m 45s
  Viewers: 15,234 (4.2x baseline)
==============================================================
Logged moment #7 at 1h 23m 45s
```

## What Happens Internally
1. Polls `https://kick.com/api/v2/channels/clavicular` every 10s
2. Maintains rolling 60-second baseline of viewer counts
3. When current viewers > baseline * 3.0, logs a "moment"
4. Moments are stored in `data/clips.db` with:
   - `stream_elapsed_seconds` - timestamp in stream
   - `viewer_count` - viewers at spike
   - `spike_ratio` - how much above baseline

## Error Handling
- If API returns 403/429: Script has built-in headers to avoid blocks
- If stream goes offline: Script waits for stream to return
- If Ctrl+C: Graceful shutdown, session marked as ended

## Output
- Console: Real-time status updates
- Database: `data/clips.db` populated with moments
- The Clipper Agent will read from this database

## Dependencies
- Requires: Network access to kick.com
- Requires: Write access to data/clips.db
- Provides: Moment timestamps for Clipper Agent
```

---

## AGENT 2: Stream Recorder Agent

### Purpose
Record the stream continuously using Streamlink. This is a manual/external process.

### Full Prompt for AI Agent

```markdown
# Stream Recorder Agent

## Your Role
You are the Stream Recorder Agent. Your job is to capture the live stream
to a video file that can later be clipped.

## Configuration
- Streamer: `clavicular`
- Quality: `best` (highest available)
- Output: `recordings/` directory

## Execution Steps

### Step 1: Ensure Directory Exists
```bash
mkdir -p "E:\Coding Projects\Clipping automater\recordings"
```

### Step 2: Start Recording
```bash
streamlink https://kick.com/clavicular best -o "E:\Coding Projects\Clipping automater\recordings\clavicular_{time:%Y%m%d_%H%M%S}.mp4"
```

### Step 3: Monitor Recording
- Streamlink will show: `[cli][info] Stream is offline` if not live
- When live: `[cli][info] Opening stream: (best) (source)`
- Recording continues until you press Ctrl+C or stream ends

## Output Filename Format
```
clavicular_20260117_143022.mp4
         │       │      │
         │       │      └── Time started (HH:MM:SS)
         │       └── Date (YYYYMMDD)
         └── Streamer name
```

## Critical Notes

### TIMING IS CRITICAL
The recording MUST start at the same time as the monitor!

If the monitor starts at stream time 0:00:00, the recording must also
start at stream time 0:00:00. Otherwise, the clip timestamps will be wrong.

**Best practice:** Start both in parallel immediately when stream goes live.

### If You Miss the Start
If recording starts late, you have two options:
1. Note the offset and adjust clip times manually
2. Restart both monitor and recording together

### Disk Space
- 1080p streams: ~3-5 GB per hour
- Ensure sufficient disk space in `recordings/`
- Delete old recordings after clipping

## Error Handling
- If stream goes offline: Streamlink stops, restart when live
- If disk full: Recording corrupts, ensure space
- If network drops: Recording may have gaps

## Dependencies
- Requires: Streamlink installed (`pip install streamlink`)
- Requires: Stream must be live
- Provides: Video file for Clipper Agent
```

---

## AGENT 3: Clip Creator Agent

### Purpose
Read unprocessed moments from SQLite and create video clips using FFmpeg.

### Full Prompt for AI Agent

```markdown
# Clip Creator Agent

## Your Role
You are the Clip Creator Agent. Your job is to take detected moments from
the database and create video clips using FFmpeg.

## Configuration
- Clip window: 30 seconds before + 30 seconds after spike
- Output: `clips/` directory
- Format: MP4 (copy codec, no re-encoding)

## Execution Steps

### Step 1: List Available Recordings
```bash
cd "E:\Coding Projects\Clipping automater"
python src/clip/create_clips.py --list
```

Output:
```
Available recordings in recordings/:
------------------------------------------------------------
  clavicular_20260117_143022.mp4 (2345.6 MB)
  clavicular_20260116_201500.mp4 (1890.3 MB)
```

### Step 2: Preview What Will Be Clipped (Dry Run)
```bash
python src/clip/create_clips.py --recording "recordings/clavicular_20260117_143022.mp4" --dry-run
```

Output:
```
Found 3 unprocessed moment(s)
============================================================

Moment #7:
  Time in stream: 1h 23m 45s
  Viewers: 15,234 (4.2x baseline)
  Clip: 1h 23m 15s - 1h 24m 15s (60s)
  Output: clavicular_moment_1h23m45s_007_20260117.mp4
  [DRY RUN] Would create clip
```

### Step 3: Create Clips
```bash
python src/clip/create_clips.py --recording "recordings/clavicular_20260117_143022.mp4"
```

Output:
```
Moment #7:
  Time in stream: 1h 23m 45s
  Running: ffmpeg -ss 00:01:23.150 -i ... -t 60 ...
  [OK] Created clavicular_moment_1h23m45s_007_20260117.mp4
```

### Step 4: Verify Clips
```bash
dir clips\
```

## FFmpeg Command Breakdown
```bash
ffmpeg -y -ss 00:01:23.150 -i input.mp4 -t 60 -c copy output.mp4
       │  │                │            │     │
       │  │                │            │     └── Copy codec (fast)
       │  │                │            └── 60 second duration
       │  │                └── Input file
       │  └── Start time (seek before input = fast)
       └── Overwrite existing
```

## Critical Notes

### Recording Must Be Complete
Do NOT run clipper while recording is still in progress.
Wait for recording to finish, or use a different recording file.

### Moment Timestamps
- Timestamps are relative to stream start (not recording start)
- Recording must start when stream starts for accurate clips
- If there's an offset, clips will be at wrong times

### Session-Specific Processing
To process only moments from a specific session:
```bash
python src/clip/create_clips.py --session 5
```

## Error Handling
- If recording not found: Script skips moment, prints warning
- If FFmpeg fails: Moment stays unprocessed, retry later
- If disk full: FFmpeg fails, ensure space

## Dependencies
- Requires: FFmpeg installed and in PATH
- Requires: Recording file from Recorder Agent
- Requires: Moments in database from Monitor Agent
- Provides: Final clip files in clips/
```

---

## PARALLEL EXECUTION STRATEGY

### Terminal Layout (3 Terminals)

```
┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 1: Monitor          │ TERMINAL 2: Recorder         │
│                              │                              │
│ $ python src/monitor/        │ $ streamlink kick.com/       │
│   realtime_monitor.py        │   clavicular best -o ...     │
│   --streamer clavicular      │                              │
│                              │                              │
│ [15:30:45] Viewers: 5,234    │ [cli] Recording to:          │
│ [15:30:55] Viewers: 5,456    │   clavicular_20260117.mp4    │
│ [15:31:05] SPIKE! 15,234     │ [download] 125.3 MiB         │
│                              │                              │
├──────────────────────────────┴──────────────────────────────┤
│ TERMINAL 3: Clipper (run after stream ends)                 │
│                                                             │
│ $ python src/clip/create_clips.py --recording ...           │
│                                                             │
│ Found 3 unprocessed moments                                 │
│ Creating clip 1/3... [OK]                                   │
│ Creating clip 2/3... [OK]                                   │
│ Creating clip 3/3... [OK]                                   │
└─────────────────────────────────────────────────────────────┘
```

### Startup Sequence

1. **When stream goes live:**
   - Terminal 1: `python src/monitor/realtime_monitor.py --streamer clavicular`
   - Terminal 2: `streamlink https://kick.com/clavicular best -o recordings/clavicular_{time:%Y%m%d_%H%M%S}.mp4`

2. **Start both simultaneously** (within seconds of each other)

3. **During stream:**
   - Monitor detects spikes, logs to database
   - Recorder captures video continuously

4. **After stream ends:**
   - Stop both (Ctrl+C)
   - Terminal 3: `python src/clip/create_clips.py --recording recordings/clavicular_XXXXXXXX.mp4`

---

## INTER-AGENT COMMUNICATION

Agents communicate through **SQLite database** (`data/clips.db`):

```
Monitor Agent                    Clipper Agent
     │                                │
     │  INSERT INTO moments           │
     │  (session_id, elapsed, ...)    │
     │  ───────────────────────────▶  │
     │                                │
     │                     SELECT * FROM moments
     │                     WHERE processed = 0
     │                                │
     │                     UPDATE moments
     │                     SET processed = 1
     │  ◀───────────────────────────  │
```

### Database Schema Reference

**sessions table:**
| Column | Type | Purpose |
|--------|------|---------|
| id | INT | Session ID |
| streamer | TEXT | Streamer name |
| started_at | DATETIME | When monitoring started |
| ended_at | DATETIME | When monitoring ended |
| recording_path | TEXT | Path to video file |
| is_active | BOOL | Currently monitoring? |

**moments table:**
| Column | Type | Purpose |
|--------|------|---------|
| id | INT | Moment ID |
| session_id | INT | FK to sessions |
| stream_elapsed_seconds | REAL | Timestamp in stream |
| viewer_count | INT | Viewers at spike |
| spike_ratio | REAL | How much above baseline |
| processed | BOOL | Has clip been created? |
| clip_path | TEXT | Path to created clip |

---

## COPY-PASTE COMMANDS

### Quick Start (All Three)

**Terminal 1 - Monitor:**
```bash
cd "E:\Coding Projects\Clipping automater"
python src/monitor/realtime_monitor.py --streamer clavicular
```

**Terminal 2 - Recorder:**
```bash
cd "E:\Coding Projects\Clipping automater"
streamlink https://kick.com/clavicular best -o "recordings/clavicular_{time:%Y%m%d_%H%M%S}.mp4"
```

**Terminal 3 - Clipper (after stream):**
```bash
cd "E:\Coding Projects\Clipping automater"
python src/clip/create_clips.py --list
python src/clip/create_clips.py --recording "recordings/YOUR_FILE.mp4"
```

### Status Check Commands

**Check database for moments:**
```bash
sqlite3 data/clips.db "SELECT id, stream_elapsed_seconds, viewer_count, spike_ratio, processed FROM moments ORDER BY id DESC LIMIT 10;"
```

**Check active sessions:**
```bash
sqlite3 data/clips.db "SELECT * FROM sessions WHERE is_active = 1;"
```

**Count unprocessed moments:**
```bash
sqlite3 data/clips.db "SELECT COUNT(*) FROM moments WHERE processed = 0;"
```

---

## Files Involved

| File | Role | Modified By |
|------|------|-------------|
| `src/monitor/realtime_monitor.py` | Monitor Agent | —  (run only) |
| `src/clip/create_clips.py` | Clipper Agent | — (run only) |
| `config/settings.py` | Configuration | User |
| `data/clips.db` | Coordination | Monitor, Clipper |
| `recordings/*.mp4` | Video storage | Recorder Agent |
| `clips/*.mp4` | Final clips | Clipper Agent |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Recording starts late → wrong timestamps | Start monitor & recorder together |
| Kick API rate limit (403/429) | Headers already configured, 10s interval |
| Disk fills up during recording | Monitor disk, delete old recordings |
| FFmpeg fails on corrupt video | Re-record, or manually specify timestamps |
| Stream goes offline mid-recording | Scripts handle gracefully, resume when live |

---

## Future Enhancements (Not In Scope)

- Chat velocity monitoring (WebSocket)
- Auto-start when stream goes live
- Cloud upload of clips
- Multi-streamer support
- Web dashboard

---

*Plan created: 2026-01-17*
*Ready for execution: Copy-paste commands above*
