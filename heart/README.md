# 💓 Heart — SuneelWorkSpace Organ

## Purpose
Orchestrates task execution workflows, goals state machines, model Fallback Routing, and DAG scheduling.

## What\s Inside
* `tasks/`: ACTIVE_TASKS.md and COMPLETED_TASKS.md logs.
* `goals/`: Dependency maps, retry queues, planners, and goal progress logs.
* `model_router/`: Model provider select algorithms and daily call quotas.
* `orchestrator/`: Mesh routing protocols and DAG runner logic.

## Key Files
* [heart/tasks/ACTIVE_TASKS.md](file:///Users/MAC/SuneelWorkSpace/heart/tasks/ACTIVE_TASKS.md): Current session task checklists.
* [heart/model_router/router.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/router.py): Best model mapping logic.
* [heart/model_router/quota_tracker.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/quota_tracker.py): Usage metrics and midnight reset logic.
* [heart/orchestrator/dag/dag_runner.py](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/dag_runner.py): Sequencer of yaml execution workflows.

## Provides (to other organs)
* Fallback model targets to execution clients.
* Scheduled pipeline workflows to `hands` and `eyes`.
* Active goal markers to morning brief compilers.

## Needs (from other organs)
* Injected context from `brain`.
* Telemetry records from `blood`.
* Binary shortcuts from `hands`.

## CLI Commands
* `model-status`: Prints models token usage and limits.
* `model-health`: Provider response latency checks.
* `goal-create`: Instantiates goal tracker files.
* `goal-plan`: Schedules step sequences and dependencies.
* `goal-status`: Goal progress summary.

## How To Add Something Here
1. Write custom workflows in `heart/orchestrator/dag/pipelines/` as YAML.
2. Add routing patterns in `heart/orchestrator/router/`.
3. Link CLI triggers in `hands/bin/`.
