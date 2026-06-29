# eyes

Web dashboard, visual monitoring, and screenshot healing.

## What It Does

- **Control Center dashboard** — FastAPI app at `http://localhost:7777` with full workspace visibility
- **6-stage execution pipeline** — Brainstorm → Plan → Confirm → Implement → Test → Wire, streamed via WebSocket
- **13 live widgets** — each auto-refreshing from API endpoints
- **Visual monitor** — screenshot capture and Ollama-powered visual repair queue
- **Approval queue** — human approval gate for controlled actions

## Dashboard

```bash
workspace-dashboard    # Start the dashboard server
```

Open `http://localhost:7777`. WebSocket client ID connects automatically.

### Widget Inventory

| Widget | Endpoint | Refresh |
|--------|----------|---------|
| Goals | `/api/goals` | 60s |
| Agent Activity | `/api/agent` | 15s |
| Memory Health | `/api/memory` | 30s |
| MCP Status | `/api/mcp` | 60s |
| Anticipation | `/api/anticipation` | 60s |
| Autolab | `/api/autolab` | 60s |
| README Health | `/api/readme-health` | 60s |
| Model Status | `/api/models/status` | 60s |
| Evolution | `/widgets/evolution` | 30s |
| Visual Monitor | `/widgets/visual` | 45s |
| Approval Queue | `/widgets/approval` | 20s |
| Ollama | `/widgets/ollama` | 60s |
| Hermes | `/widgets/hermes` | 60s |
| Nerve System | `/widgets/nerve` | 30s |
| Test Suite | `/widgets/tests` | 120s |

### API Routes

```
GET  /api/health           System health score
GET  /api/tests/status     Latest test run results
POST /api/tests/run        Trigger test run (background)
POST /api/tests/repair-loop Trigger autonomous repair loop (background)
POST /api/health/repair    Launch 8-stage health repair pipeline
GET  /api/nerve/status     All 12 organ nerve status
GET  /api/models/rotation  Model rotation stats
GET  /api/health/trend     Health score trend (last 10 checks)
GET  /api/ollama/status    Ollama server + model list
GET  /api/hermes/status    Hermes agent version + skill count
```

### Quick Actions (Toolbar)

Night Shift · Gap Scan · Challenge · Screenshot · Models · Evolution · Morning Brief · CI

## Key Files

| File | Purpose |
|------|---------|
| `eyes/dashboard/server.py` | FastAPI app (33.7KB) — all routes, WebSocket, pipeline |
| `eyes/dashboard/index.html` | Dashboard UI with HTMX panels |
| `eyes/dashboard/static/dashboard.js` | JS: WebSocket, polling, runTests(), runRepairLoop() |
| `eyes/dashboard/pipeline/pipeline.py` | 6-stage execution pipeline |
| `eyes/dashboard/widgets/nerve_monitor.py` | Organ health widget (filesystem checks) |
| `eyes/dashboard/widgets/hermes_status.py` | Hermes agent status (HTML-escaped output) |
| `eyes/dashboard/widgets/ollama_status.py` | Ollama model list widget |
| `eyes/dashboard/widgets/model_status.py` | Model rotation + quota widget |
| `eyes/visual/screenshot_manager.py` | Screenshot capture and listing |
| `eyes/visual/visual_repair_agent.py` | Ollama-powered visual repair |

## Security Notes

- WebSocket connections validated against `_ALLOWED_ORIGINS` (`localhost:7777`, `127.0.0.1:7777`)
- Quick actions validated against server-side `_QUICK_ACTIONS` allowlist (no shell interpolation)
- All widget HTML uses `html.escape()` on user-derived values (XSS protection)

## Tests

Covered by `tests/organs/eyes/test_eyes.py` — part of the 103/103 passing suite.

## Nerve Events

```python
notify_change("eyes", "dashboard_started", "eyes/dashboard/server.py")
```

*Updated: 2026-06-28*
