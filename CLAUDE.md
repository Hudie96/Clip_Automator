# Project Memory

> Keep this file under 200 lines. Use `@path/to/file` imports for detailed rules.

## Quick Reference

**Commands (Multi-Terminal Workflow):**
```bash
# Terminal 1: Monitor stream for viral moments
python realtime_monitor.py

# Terminal 2: Record stream continuously
streamlink https://kick.com/clavicular best -o recordings/clavicular_{time:%Y%m%d_%H%M%S}.mp4

# Terminal 3: Create clips from timestamps
python create_clips.py
```

## Project Overview

Real-time stream clipping automation tool for Kick.com. Monitors a streamer's viewer count for "viral moment" spikes, records the stream continuously, and auto-generates clips when significant events are detected. Future plans include chat velocity analysis for better detection.

## Tech Stack

- **Language:** Python 3.x
- **Recording:** Streamlink (stream capture)
- **Clipping:** FFmpeg (video processing)
- **API:** Kick.com API (viewer count, stream status)
- **Future:** WebSocket for chat monitoring

## Key Directories

```
├── recordings/        # Raw stream recordings (LARGE - ignored by Claude)
├── clips/             # Generated clips (LARGE - ignored by Claude)
├── src/
│   ├── monitor/       # Stream monitoring scripts
│   ├── clip/          # Clipping logic
│   └── utils/         # Helpers (timestamp conversion, etc.)
├── config/            # Configuration files
└── logs/              # Monitoring logs
```

## Multi-Terminal Workflow

This project requires **multiple terminals running simultaneously**:

| Terminal | Purpose | Command |
|----------|---------|---------|
| 1 | Monitor viewer spikes | `python realtime_monitor.py` |
| 2 | Record stream | `streamlink https://kick.com/clavicular best -o ...` |
| 3 | Process clips | `python create_clips.py` |

Claude's role: **Plan workflows and provide terminal commands** to copy-paste.

## Code Standards

### Style
- Python 3.x with type hints where helpful
- Use `requests` for HTTP calls
- Use `subprocess` for FFmpeg/Streamlink calls
- 4-space indentation (Python standard)

### Naming
- Scripts: snake_case (`realtime_monitor.py`)
- Functions: snake_case (`create_clip()`)
- Constants: SCREAMING_SNAKE_CASE (`SPIKE_THRESHOLD = 3`)
- Classes: PascalCase (`StreamMonitor`)

### Error Handling
- Always handle network errors (stream goes offline)
- Log timestamps for debugging
- Graceful shutdown on Ctrl+C

## Workflow Rules

### Before Coding
1. Read the task requirements fully
2. Plan which terminals need which commands
3. Consider edge cases (stream offline, API rate limits)

### During Development
- Test with short recordings first
- Verify FFmpeg commands before full runs
- Log everything for debugging

### Constraints
- **NEVER read video files** (too large, useless to Claude)
- No API keys in code (use `.env`)
- Keep monitoring scripts lightweight

## Do NOT

- Edit files in `venv/` or `__pycache__/`
- Read/write video files directly
- Store Kick API keys in code
- Create clips without timestamps
- Run FFmpeg on files that don't exist

## Agentic Loop Architecture

```
1. Gather Context → 2. Autonomous Action → 3. Verify & Correct
                                                    ↓
                                            Pass = Done
                                            Fail = Loop back
```

### Model Selection
| Task | Model | Why |
|------|-------|-----|
| Planning multi-terminal workflows | Opus | Complex coordination |
| Writing Python scripts | Sonnet | Fast, reliable |
| Quick command lookups | Haiku | Cheap, very fast |

### Key Commands
| Command | Purpose |
|---------|---------|
| `/plan` | Plan multi-step workflows |
| `/agent [task]` | Run master agent for complex tasks |
| `/verify` | Run verification checks |
| `/explain` | Understand how code works |

## Detection Signals (Future)

Current: Viewer count spikes (3x baseline)

Planned improvements:
- Chat message velocity (messages/second)
- Specific emote spam detection
- "CLIP THAT" message detection
- Donation/sub alert triggers

## Reference Documentation

- @.claude/rules/error-handling.md
- @.claude/rules/git-workflow.md
- @.claude/docs/AGENTIC-LOOP.md

---

*Last updated: 2026-01-17*
*Configured for: Real-time Kick.com stream clipping*
