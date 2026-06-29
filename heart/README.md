# heart

Goal scheduling, task queue management, and model routing.

## What It Does

- **Task queues** — `ACTIVE_TASKS.md`, `TASK_QUEUE.md`, `COMPLETED_TASKS.md` track all work
- **Goal engine** — create, execute, monitor, and complete goals with full lifecycle management
- **Model router** — selects the best Ollama/cloud model for each task type
- **Model rotator** — scores models by time-of-day, task affinity, and recent availability
- **Model health checker** — verifies which models are reachable before routing
- **Orchestrator** — DAG-based multi-model mesh routing for complex multi-step tasks

## Key Files

| File/Dir | Purpose |
|----------|---------|
| `heart/tasks/ACTIVE_TASKS.md` | Current in-progress tasks |
| `heart/tasks/TASK_QUEUE.md` | Queued tasks (populated by suggestion_consumer) |
| `heart/tasks/COMPLETED_TASKS.md` | Finished tasks log |
| `heart/model_router/router.py` | Routes tasks to best model; returns model dict |
| `heart/model_router/model_rotator.py` | Scores models by task type + time of day |
| `heart/model_router/health_checker.py` | Checks model availability |
| `heart/model_router/quota_tracker.py` | Tracks API quota usage |
| `heart/goals/` | Goal lifecycle scripts (create, execute, monitor, complete) |
| `heart/orchestrator/` | DAG + mesh routing for multi-step pipelines |

## Model Router

The router selects from 6 Ollama models + cloud fallbacks:

| Model | Strengths | Used For |
|-------|-----------|----------|
| `suneelworkspace` | Workspace-aware (llama3.3:70b base, rich system prompt) | General, repair, curation |
| `codellama` | Code analysis | Code review, pre-commit hooks |
| `llama3.3:70b` | Heavy reasoning | Complex analysis |
| `llama3.1` | Balanced | Learning, memory |
| `mistral` | Security analysis | Security scanning |
| `llama3.2` | Fast, lightweight | Quick queries |

`get_best_model(task_type)` and `get_best_model_for_task(task_type)` both return model dicts with `{"id": ..., "score": ...}`.

## CLI Commands

```bash
model-route              # Route a task to best model
model-health             # Check all model availability
model-rotate             # Get best model for a task type
model-status             # View quota and rotation stats
goal-create              # Create a new goal
goal-status              # View active goals
goal-execute             # Execute a goal step
goal-complete            # Mark goal complete
goal-monitor             # Monitor goal progress
goal-plan                # Generate a goal execution plan
route-task               # Route + execute a task through mesh
```

## Suggestion Consumer Integration

`lab/autolab/suggestion_consumer.py` runs every 2h and writes SAFE high-confidence suggestions directly to `TASK_QUEUE.md`. This closes the Ollama output→action loop — suggestions no longer die in log files.

## Tests

Covered by `tests/organs/heart/test_heart.py` — part of the 103/103 passing suite.  
Key assertions: `router.py` returns model dict (not string), `model_rotator.py` imports and scores correctly.

## Nerve Events

```python
notify_change("heart", "task_created", "heart/tasks/TASK_QUEUE.md")
notify_change("heart", "model_selected", "codellama")
```

*Updated: 2026-06-28*
