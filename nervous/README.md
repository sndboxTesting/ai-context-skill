# nervous

Central event bus, nerve propagator, organ registry, MCP connectors, and nerve healer.

## What It Does

- **Nerve propagator** — inter-organ event bus: all 12 organs publish and subscribe here
- **Nerve healer** — Ollama-powered auto-healer detects and repairs broken nerve connections
- **Nerve registry** — `nerve_registry.json` maps all 12 organs and their dependencies
- **MCP connectors** — gateway to Claude, Codex, and other model connectors
- **Nerve status** — `nerve_status.py` checks all 12 organ statuses
- **Nerve inbox** — per-organ event inbox dirs (gitignored; runtime only)

## Key Files

| File | Purpose |
|------|---------|
| `nervous/nerve_propagator.py` | Event bus: `notify_change()` + `get_status()` |
| `nervous/nerve_healer.py` | Auto-healer (Ollama): detects + repairs broken connections |
| `nervous/nerve_registry.json` | Registry of all 12 organs, their `provides` + `needs` |
| `nervous/nerve_status.py` | Prints organ statuses |
| `nervous/gateway/` | MCP gateway |
| `nervous/mcp/` | MCP connectors (Claude, Codex) |
| `nervous/skills/` | Nerve skills |

## API

```python
from nervous.nerve_propagator import notify_change, get_status

# Publish an event
payload = notify_change("brain", "memory_updated", "brain/memory/MEMORY.md")
# payload["event_type"] == "memory_updated"  (not "change_type")

# Get health status of all 12 organs
status = get_status()
# → {"brain": {"healthy": True, ...}, "heart": {...}, ...}
```

**Key**: returned payloads use `event_type` — not `change_type`.

## Nerve.json Format (v1.1)

Every organ has a `nerve.json` at its root:

```json
{
  "version": "1.1",
  "organ": "brain",
  "provides": ["memory", "search", "context"],
  "needs": ["spine/state", "heart/tasks"],
  "key_files": ["brain/memory/MEMORY.md"],
  "cli_commands": ["memory-search", "memory-curate"]
}
```

## Nerve Healer

`nervous/nerve_healer.py` runs every 6h via `lab/autolab/ollama_orchestrator.py`:
- Calls `get_status()` to check all 12 organs
- Asks `suneelworkspace` model for SAFE repair suggestions
- Applies SAFE fixes; symlink fixes always queued for human review
- Logs all actions to `blood/logs/nerve_healer.jsonl`

## CLI Commands

```bash
nerve-status   # Print all 12 organ statuses
nerve-heal     # Run Ollama nerve healer
nerve-check    # Quick filesystem check of all nerve.json files
```

## Tests

Covered by `tests/nerve_system/test_nervous.py` — part of the 103/103 passing suite.

Key assertion: `notify_change()` returns `event_type` in payload (not `change_type`).

## Dependencies

- `spine/` (for CURRENT_STATE.json)

*Updated: 2026-06-28*
