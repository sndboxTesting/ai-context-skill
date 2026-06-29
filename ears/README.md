# ears

External RSS/GitHub monitors, morning brief builder, and personalized digest.

## What It Does

- **Monitor runner** — polls RSS feeds, GitHub notifications, and custom sources on a schedule
- **Digest builder** — assembles structured daily digest from all monitor outputs
- **Personalized brief** — Ollama-scored, priority-ranked morning brief matching Suneel's interests
- **Morning brief CLI** — `morning-brief` and `morning-brief-personal` commands

## Key Files

| File/Dir | Purpose |
|----------|---------|
| `ears/monitor_runner.py` | Runs all monitors (RSS, GitHub) on schedule |
| `ears/digest_builder.py` | Assembles digest from monitor outputs |
| `ears/personalized_brief.py` | Ollama-powered personal scoring + ranking |
| `ears/monitors/` | Individual monitors (RSS, GitHub, custom) |
| `ears/briefs/` | Historical brief archives |
| `ears/nerve.json` | Organ manifest v1.1 |

## CLI Commands

```bash
morning-brief             # Build daily digest from all sources
morning-brief-personal    # Personalized digest with Ollama relevance scoring
monitor-run               # Run all monitors (one-shot)
monitor-status            # Show last monitor run results
```

## Data Flow

```
External sources (RSS, GitHub)
  → ears/monitors/
  → digest_builder.py → digest.json
  → personalized_brief.py (Ollama scoring)
  → morning brief output
```

## Tests

Covered by `tests/organs/ears/test_ears.py` — part of the 103/103 passing suite.

## Nerve Events

```python
notify_change("ears", "brief_built", "ears/briefs/")
notify_change("ears", "monitor_run_complete", "ears/")
```

*Updated: 2026-06-28*
