# blood

Telemetry SQLite databases, all workspace logs (JSONL), and anomaly detection.

## What It Does

- **Log sink** — every agent, engine, and script appends structured JSONL to `blood/logs/`
- **SQLite telemetry** — `blood/telemetry/` stores metrics, performance, and event history
- **Anomaly detection** — `blood/telemetry/anomaly_detector.py` flags unusual patterns
- **Log query** — `blood/telemetry/log_query.py` queries both SQLite and JSONL
- **Controlled queues** — LLM-suggested destructive actions land here for human review before any execution

## Key Log Files

| File | Written By | Purpose |
|------|-----------|---------|
| `blood/logs/SESSION_LOG.md` | All agents | Human-readable session summaries |
| `blood/logs/pre_commit_review.jsonl` | `pre_commit_hook.sh` | codellama code review results |
| `blood/logs/nerve_events.jsonl` | `nerve_propagator.py` | All organ nerve events |
| `blood/logs/execution_history.jsonl` | Dashboard pipeline | 6-stage execution history |
| `blood/logs/ollama_suggestions.md` | All Ollama engines | Raw LLM suggestions |
| `blood/logs/code_review_report.md` | `code_review_engine.py` | Python file analysis |
| `blood/logs/nerve_healer.jsonl` | `nerve_healer.py` | Organ healing events |
| `blood/logs/repair_loop.jsonl` | `autonomous_repair_loop.py` | Test repair iterations |
| `blood/logs/repair_loop_controlled_queue.json` | Repair loop | LLM symlink fixes — queued for human review |
| `blood/logs/suggestion_controlled_queue.json` | `suggestion_consumer.py` | Low-confidence suggestions — queued for review |

## Gitignored Log Files

These are high-churn runtime files excluded from git (see `.gitignore`):

- `blood/logs/readme_intelligence.log` — rewritten every 30 min by auto-sync
- `tests/reports/junit_*.xml` — JUnit XML from pytest runs
- `blood/logs/repair_loop.jsonl` — high-volume test repair logs

## SQLite Telemetry

```
blood/telemetry/
  telemetry.db          # Main metrics database
  log_query.py          # Query telemetry + JSONL logs
  anomaly_detector.py   # Flag unusual patterns
```

## Controlled Queues

LLM-generated destructive actions are **never** auto-applied. They land here first:

- **Symlink fixes** (from repair loop) → `blood/logs/repair_loop_controlled_queue.json`
- **Low-confidence suggestions** (from suggestion_consumer) → `blood/logs/suggestion_controlled_queue.json`

Review and apply manually, or use the Approval Queue widget in the dashboard at `http://localhost:7777`.

## Tests

Covered by `tests/organs/blood/test_blood.py` — part of the 103/103 passing suite.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("blood", "log_written", "blood/logs/SESSION_LOG.md")
notify_change("blood", "anomaly_detected", "blood/telemetry/anomaly_detector.py")
```

*Updated: 2026-06-28*
