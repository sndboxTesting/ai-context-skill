# spine

Workspace health state, diagnostics, audit, backups, and README intelligence.

## What It Does

- **Health state** — `CURRENT_STATE.json` and `WORKSPACE_HEALTH.json` track live workspace state
- **Diagnostics** — `spine/diagnostics/diagnostic_scheduler.py` runs periodic health checks
- **Audit** — `spine/audit/` logs workspace-wide audits and decisions
- **Backups** — `spine/backups/` and `spine/snapshots/` hold periodic state backups
- **README intelligence** — tracks README freshness across all organs (auto-updates every 30 min)
- **Enhancement logger** — `spine/enhancement_logger.py` records workspace improvements

## Key Files

| File/Dir | Purpose |
|----------|---------|
| `spine/state/CURRENT_STATE.json` | Live workspace state (agent, tasks, health) |
| `spine/state/WORKSPACE_HEALTH.json` | Health score, issues list, organ statuses |
| `spine/enhancement_logger.py` | Records enhancements and improvements |
| `spine/diagnostics/diagnostic_scheduler.py` | Periodic health check scheduler |
| `spine/audit/` | Audit logs and decision records |
| `spine/backups/` | Periodic state backups |
| `spine/snapshots/` | Point-in-time workspace snapshots |
| `spine/readme_health_cache.json` | Cached README health scores |
| `spine/readme_metrics_history.json` | README health score history |
| `spine/readme_dependency_map.json` | Cross-README dependency graph |
| `spine/readme_repair_report.json` | Last README repair analysis |
| `spine/readme_self_reflection.json` | README system self-assessment |
| `spine/readme_policy.json` | README update policy rules |
| `spine/readme_priority_queue.json` | READMEs queued for update |

## CURRENT_STATE.json

Written by `agent-start` / `agent-finish` / `agent-doctor`:

```json
{
  "session_id": "...",
  "agent": "claude-code",
  "active_tasks": [...],
  "last_updated": "...",
  "health_score": 0-100,
  "open_issues": [...]
}
```

## WORKSPACE_HEALTH.json

Updated by diagnostic runs and `agent-doctor`:

```json
{
  "health_score": 0-100,
  "issues": [
    {"organ": "...", "severity": "low|medium|high", "description": "..."}
  ],
  "organs": {
    "brain": {"healthy": true, ...},
    ...12 organs
  },
  "last_check": "..."
}
```

## README Intelligence

The README intelligence system tracks and auto-updates README freshness:
- Detects stale auto-generated content ("Basic workspace component")
- Tracks last meaningful update per organ
- Feeds the `/api/readme-health` dashboard widget
- Background auto-sync runs every 30 min (logs to `blood/logs/readme_intelligence.log`)
- Policy defined in `spine/readme_policy.json`

## Diagnostics

`spine/diagnostics/diagnostic_scheduler.py` checks:
- All 12 organ `nerve.json` files present and valid (v1.1)
- Key files exist: MEMORY.md, DECISIONS.md, ACTIVE_TASKS.md, SESSION_HANDOFF.md
- Ollama reachable on port 11434
- Symlink integrity in `hands/bin/` (194 symlinks)
- Test suite green

```bash
agent-doctor    # Run full diagnostic → update WORKSPACE_HEALTH.json
```

## Dependencies

- `nervous/` depends on `spine/state/` for org status reads

## Tests

Covered by `tests/organs/spine/test_spine.py` — part of the 103/103 passing suite.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("spine", "health_updated", "spine/state/WORKSPACE_HEALTH.json")
notify_change("spine", "diagnostic_complete", "spine/diagnostics/")
```

*Updated: 2026-06-28*
