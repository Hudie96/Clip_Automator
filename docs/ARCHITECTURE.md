# Web App Architecture

This document outlines the future architecture for scaling Clip Automater to a multi-user SaaS product.

## Current Architecture (Local)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL MACHINE                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────┐    ┌─────────────────────────────┐              │
│  │  Flask Dashboard        │◄───│  Real-time Clipper          │              │
│  │  (port 5000)            │    │  - FFmpeg segments          │              │
│  │                         │    │  - Chat/Viewer triggers     │              │
│  │  - Live stats           │    │  - Clip creation            │              │
│  │  - Clip review          │    └─────────────────────────────┘              │
│  │  - Fullscreen slideshow │                                                 │
│  │  - Video player         │    ┌─────────────────────────────┐              │
│  │  - Streamer search      │    │  VOD Clipper                │              │
│  │  - VOD browser          │    │  - Download VOD segments    │              │
│  │  - Clip editor          │    │  - Chat replay analysis     │              │
│  └───────────┬─────────────┘    │  - Auto-detect highlights   │              │
│              │                  └─────────────────────────────┘              │
│              ▼                                                                │
│  ┌─────────────────┐    ┌─────────────────────────────┐                      │
│  │  SQLite         │    │  Local Storage              │                      │
│  │  (data/clips.db)│    │  - clips/                   │                      │
│  │                 │    │  - segments/                │                      │
│  │  - Sessions     │    │  - thumbnails               │                      │
│  │  - Moments      │    │  - vod_cache/               │                      │
│  │  - Clips        │    └─────────────────────────────┘                      │
│  │  - Streamers    │                                                         │
│  └─────────────────┘                                                         │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Future Architecture (Multi-User SaaS)

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  Next.js / React SPA                                        │
│  - Dashboard, clip review, settings                         │
│  - Video player with clip editor                            │
│  - User authentication (Clerk/Auth0)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ REST/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                      API LAYER                              │
│  FastAPI / Flask                                            │
│  - Auth middleware (JWT)                                    │
│  - Clip management                                          │
│  - Streamer config                                          │
│  - WebSocket for live stats                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    WORKER LAYER                             │
│  Celery / Background Tasks                                  │
│  - Per-streamer clipper instances                           │
│  - Upload workers (YouTube, TikTok)                         │
│  - Cleanup workers                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     STORAGE                                 │
│  - PostgreSQL (metadata, users, settings)                   │
│  - S3/Backblaze B2 (video clips, thumbnails)               │
│  - Redis (session, cache, pub/sub)                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Current API Endpoints (Local)

#### Clip Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/clips/<filename>` | DELETE | Delete a clip and its thumbnail |
| `/api/clips/<filename>` | PATCH | Rename a clip (`new_name` in body) |
| `/api/clips/<filename>/favorite` | POST | Toggle favorite status |
| `/api/clips/<filename>/metadata` | GET | Get clip metadata (duration, dimensions) |
| `/api/favorites` | GET | List all favorited clips |
| `/api/clips/trim` | POST | Trim clip with in/out points (async job) |
| `/api/clips/trim/status/<job_id>` | GET | Check trim job status and get output |

#### Streamer Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/streamers/search` | GET | Search Kick for streamers (`?q=query&limit=10`) |
| `/api/streamers/add` | POST | Add streamer to monitoring |
| `/api/streamers/<name>` | DELETE | Remove from monitoring |
| `/api/streamers/list` | GET | List monitored streamers with live status |
| `/api/streamers/<name>/status` | GET | Get specific streamer's live status |

#### VOD Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vods/list/<streamer>` | GET | List VODs for a streamer (`?limit=20`) |
| `/api/vods/details/<vod_id>` | GET | Get detailed info about a specific VOD |
| `/api/vods/clip` | POST | Create clip from VOD (manual mode, free) |
| `/api/vods/clip/status/<job_id>` | GET | Check VOD clip job status |
| `/api/vods/analyze/<vod_id>` | POST | Analyze VOD for highlights (premium, 1 credit) |
| `/api/vods/clip/batch` | POST | Create multiple clips from highlights |
| `/api/vods/clip/batch/<batch_id>` | GET | Check batch clip job status |

#### Review Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/review/pending` | GET | Get clips pending review (`?streamer=name&limit=50`) |
| `/api/review/stats` | GET | Get review statistics (pending/approved/rejected counts) |
| `/api/review/<id>/approve` | POST | Approve a clip (optional `notes` in body) |
| `/api/review/<id>/reject` | POST | Reject a clip (optional `notes` in body) |
| `/api/review/<id>` | DELETE | Delete clip immediately (file + database) |
| `/api/review/bulk` | POST | Bulk approve/reject (`action` + `clip_ids` in body) |

### Future API Layer (SaaS)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/*` | - | Authentication (Clerk/Auth0 webhook) |
| `/api/streamers` | CRUD | Manage monitored streamers |
| `/api/clips` | GET/DELETE | Clip management |
| `/api/clips/:id/review` | POST | Approve/reject clips |
| `/api/uploads` | POST | Queue clip for upload |
| `/ws/stats` | WebSocket | Real-time stats per streamer |

### New Components (v2.0)

#### VOD Module (`src/vod/`)
| File | Purpose |
|------|---------|
| `vod_clipper.py` | Download VOD segments and create clips |
| `chat_analyzer.py` | Analyze chat replay to find highlight moments |

#### Clip Editor (`src/clip/editor.py`)
| Function | Purpose |
|----------|---------|
| `trim_clip()` | Trim clip with in/out points using FFmpeg |
| `get_metadata()` | Extract clip duration and format info |
| `preview_trim()` | Generate preview of trimmed section |

#### Streamer Search (`src/web/streamer_search.py`)
| Function | Purpose |
|----------|---------|
| `search_kick()` | Search Kick API for streamers by name |
| `get_live_status()` | Check if streamer is currently live |
| `add_streamer()` | Add streamer to monitoring config |

### Worker Types (Future SaaS)

| Worker | Responsibility |
|--------|----------------|
| `clipper-worker` | Per-streamer FFmpeg + triggers |
| `upload-worker` | YouTube/TikTok uploads |
| `cleanup-worker` | Delete rejected clips, old segments |
| `thumbnail-worker` | Generate thumbnails async |
| `vod-worker` | Process VOD clip requests |
| `analysis-worker` | Analyze VOD chat for highlights |

### Storage Strategy

| Data | Storage | Retention |
|------|---------|-----------|
| User data | PostgreSQL | Permanent |
| Clip metadata | PostgreSQL | Permanent |
| Video files | Backblaze B2 | Per plan (7/30/90 days) |
| Thumbnails | Backblaze B2 | Same as video |
| Segments | Local/Ephemeral | 2 minutes (rolling buffer) |
| Session cache | Redis | 24 hours |

## Deployment Options

### Option A: Single VPS (Starting Point)

**Pros**: Simple, low cost (~$20/mo)
**Cons**: Limited scalability, single point of failure

```
VPS (4 CPU, 8GB RAM)
├── Docker Compose
│   ├── api (Flask/FastAPI)
│   ├── worker (Celery)
│   ├── postgres
│   ├── redis
│   └── nginx
└── Backblaze B2 (external)
```

### Option B: Kubernetes (Scaling)

**Pros**: Auto-scaling, high availability
**Cons**: Complexity, higher cost (~$100+/mo)

```
K8s Cluster
├── Ingress (nginx)
├── API Deployment (3 replicas)
├── Worker StatefulSet (per streamer)
├── PostgreSQL (managed)
├── Redis (managed)
└── S3/B2 (external)
```

## Cost Analysis

### Per-User Estimates

| Service | Cost/User/Month |
|---------|-----------------|
| Compute (shared) | $2-5 |
| Storage (10GB avg) | $0.06 |
| Bandwidth (50GB avg) | $0.50 |
| Database (shared) | $0.50 |
| **Total** | **$3-6** |

### Pricing Tiers

| Tier | Price | Features | Margin |
|------|-------|----------|--------|
| Free | $0 | 1 streamer, 10 clips/day, 7-day retention | N/A |
| Creator | $9/mo | 3 streamers, 50 clips/day, 30-day retention | ~50% |
| Pro | $29/mo | 10 streamers, unlimited, 90-day, auto-upload | ~70% |

## Migration Roadmap

### Phase 1: Authentication (Week 1-2)
- [ ] Integrate Clerk/Auth0
- [ ] Add user model to database
- [ ] Protect API endpoints

### Phase 2: Cloud Storage (Week 2-3)
- [ ] Set up Backblaze B2
- [ ] Migrate clip storage to cloud
- [ ] Update clip URLs to signed URLs

### Phase 3: Deployment (Week 3-4)
- [ ] Dockerize application
- [ ] Set up VPS with Docker Compose
- [ ] Configure nginx/SSL

### Phase 4: Payments (Week 4-5)
- [ ] Integrate Stripe
- [ ] Implement plan limits
- [ ] Add usage tracking

### Phase 5: Multi-Tenant (Week 5-6)
- [ ] Isolate clips per user
- [ ] Rate limiting
- [ ] Usage dashboards

## Security Considerations

- [ ] Signed URLs for video access (expire in 1 hour)
- [ ] Rate limiting per user/IP
- [ ] Input validation on all endpoints
- [ ] Secrets in environment variables (never in code)
- [ ] HTTPS everywhere
- [ ] CORS configured properly

## Monitoring

- [ ] Application logs (structured JSON)
- [ ] Error tracking (Sentry)
- [ ] Metrics (Prometheus/Grafana or simple uptime checks)
- [ ] Alerting on:
  - API errors > 1%
  - Worker queue depth > 100
  - Disk usage > 80%
  - Memory usage > 90%

## Dashboard Features

### Tab-Based Navigation

The dashboard provides a 5-tab interface for managing all aspects of clip automation:

| Tab | Description |
|-----|-------------|
| **Dashboard** | Live stream preview, real-time stats (viewers, chat velocity, triggers), recent activity feed |
| **All Clips** | Browse all clips with thumbnails, hover-to-preview video, filter by streamer/trigger type |
| **VODs** | Browse past broadcasts, create clips manually or use auto-detect mode with chat analysis |
| **Streamers** | Search Kick API for live streamers, add/remove from monitoring list, view live status |
| **Review** | Approve/reject pending clips, fullscreen slideshow mode with keyboard shortcuts |

### Fullscreen Slide Deck Review

Review clips one-by-one in a fullscreen modal with keyboard shortcuts:

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

Trim clips with precise in/out points:

| Key | Action |
|-----|--------|
| `I` | Set in-point (trim start) |
| `O` | Set out-point (trim end) |
| `P` | Preview trim |
| `Space` | Play/pause |
| `←` `→` | Seek 5 seconds |
| `Esc` | Close editor |

### Responsive Layout

- Dashboard fits on screen without scrolling
- Collapsible stream preview panel
- Mobile-friendly navigation

---

## Open Questions

1. **Clip ownership**: Should users be able to share clips publicly?
2. **AI features**: Worth the cost for auto-highlighting? (~$0.01/clip)
3. **Platform support**: Twitch? YouTube Gaming? Just Kick?
4. **Mobile app**: Native or PWA?
