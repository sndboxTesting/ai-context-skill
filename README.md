# 🧠 SuneelWorkSpace

## EXECUTIVE SUMMARY
* **Human Body Architecture**: The workspace is structured as a living organism with 12 distinct organs, each having a single clear purpose, fully decoupled yet connected via a centralized nervous system.
* **Nerve Propagation**: Event-driven communication routes state changes and notifications automatically to dependent organs through inbox messaging.
* **Model Router with Fallback**: A quota-aware router that dynamically forwards tasks to the optimal model (Claude 3.5 Sonnet, Claude 3 Opus, GPT-4o, Gemini 2.5 Pro) with automatic fallback upon failure or quota exhaustion.
* **Control Center Dashboard**: A Web UI dashboard (port 7777) featuring panels for goal tracking, agent activity, model routing metrics, and an autonomous health repair pipeline.
* **Autonomous Evolution Engine**: A background daemon that continuous scans the workspace for capability gaps, generates self-improvement challenges, and queues autolab experiments.
* **Stateful Memory & Context**: Programmatic vector memory store (ChromaDB) and knowledge graph integrated with Obsidian brain vaults and context-injectors for zero-drift agent alignment.

---

## HUMAN BODY ARCHITECTURE

SuneelWorkSpace is organized as a human body. Every folder is an organ with a single clear purpose. Everything is connected through a nervous system. One change anywhere propagates to all dependent organs automatically.

### The 12 Organs

| Organ | Folder | Purpose | Key Files |
|---|---|---|---|
| 🧠 **Brain** | [brain/](file:///Users/MAC/SuneelWorkSpace/brain) | Long-term memory, vector store, intent prediction, knowledge graph, and research engine | [MEMORY.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/MEMORY.md), [DECISIONS.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/DECISIONS.md), [semantic_search.py](file:///Users/MAC/SuneelWorkSpace/brain/memory/vector/semantic_search.py), [prediction_engine.py](file:///Users/MAC/SuneelWorkSpace/brain/anticipation/prediction_engine.py) |
| 💓 **Heart** | [heart/](file:///Users/MAC/SuneelWorkSpace/heart) | Task orchestration, model fallback router, goal planner and task dependency engine | [router.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/router.py), [quota_tracker.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/quota_tracker.py), [mesh_monitor.py](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/mesh/mesh_monitor.py), [ACTIVE_TASKS.md](file:///Users/MAC/SuneelWorkSpace/heart/tasks/ACTIVE_TASKS.md) |
| 👁️ **Eyes** | [eyes/](file:///Users/MAC/SuneelWorkSpace/eyes) | Control Center UI dashboard, visual monitor daemon, and screenshot repair loop | [server.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/server.py), [style.css](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/static/style.css), [visual_repair_agent.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/visual_repair_agent.py), [health_repair_pipeline.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/execution/health_repair_pipeline.py) |
| 👂 **Ears** | [ears/](file:///Users/MAC/SuneelWorkSpace/ears) | World monitor fetching GitHub, RSS, and Arxiv feeds to compile daily morning briefs | [monitor_runner.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/monitor_runner.py), [digest_builder.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/digest/digest_builder.py), [arxiv_monitor.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/sources/arxiv_monitor.py) |
| 🫀 **Nervous** | [nervous/](file:///Users/MAC/SuneelWorkSpace/nervous) | Event propagator, central nerve registry, REST API gateway, and MCP server | [nerve_propagator.py](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_propagator.py), [nerve_registry.json](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_registry.json), [main.py](file:///Users/MAC/SuneelWorkSpace/nervous/mcp/server/main.py), [api.py](file:///Users/MAC/SuneelWorkSpace/nervous/gateway/api.py) |
| 🦴 **Skeleton** | [skeleton/](file:///Users/MAC/SuneelWorkSpace/skeleton) | Shared system policy instructions, safety boundaries, and session checklists | [AGENT_SYSTEM.md](file:///Users/MAC/SuneelWorkSpace/skeleton/rules/AGENT_SYSTEM.md), [IDENTITY.md](file:///Users/MAC/SuneelWorkSpace/skeleton/rules/IDENTITY.md), [SAFETY_BOUNDARIES.md](file:///Users/MAC/SuneelWorkSpace/skeleton/rules/SAFETY_BOUNDARIES.md) |
| 🩸 **Blood** | [blood/](file:///Users/MAC/SuneelWorkSpace/blood) | telemetry writing/querying, SQLite analytics db, logs, and anomaly detection | [telemetry_writer.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_writer.py), [telemetry_anomaly.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_anomaly.py), [SESSION_LOG.md](file:///Users/MAC/SuneelWorkSpace/blood/logs/SESSION_LOG.md), [telemetry.db](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry.db) |
| 🤲 **Hands** | [hands/](file:///Users/MAC/SuneelWorkSpace/hands) | CLI executable binary links, Cron/Launchd automation scripts, hooks, and CI pipelines | [workspace-changes](file:///Users/MAC/SuneelWorkSpace/hands/bin/workspace-changes), [common.sh](file:///Users/MAC/SuneelWorkSpace/hands/automation/maintenance/common.sh), [workspace_ci.py](file:///Users/MAC/SuneelWorkSpace/hands/automation/ci/workspace_ci.py) |
| 👄 **Mouth** | [mouth/](file:///Users/MAC/SuneelWorkSpace/mouth) | Natural language command dispatcher (intent classifier) and outbound comms (Mail, iMessage) | [ws.py](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/ws.py), [intent_map.json](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/intent_map.json), [mail-accounts](file:///Users/MAC/SuneelWorkSpace/mouth/comms/mail/scripts/mail-accounts) |
| 🧬 **DNA** | [dna/](file:///Users/MAC/SuneelWorkSpace/dna) | Core identity prompting files, tone profile, decision profile, and adaptive learning logic | [identity_prompt.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/prompts/identity_prompt.md), [tone_profile.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/profile/tone_profile.md), [adaptive_identity.py](file:///Users/MAC/SuneelWorkSpace/dna/identity/adaptive/adaptive_identity.py) |
| 🔬 **Lab** | [lab/](file:///Users/MAC/SuneelWorkSpace/lab) | Autolab experiments, challenger generator, evolution loop, and test harnesses | [runner.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/runner.py), [evaluator.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/evaluator.py), [engine.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/engine.py), [challenger.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/challenger.py) |
| 📋 **Spine** | [spine/](file:///Users/MAC/SuneelWorkSpace/spine) | System profile context, workspace health scoring, resource maps, snapshots, and backups | [CURRENT_STATE.json](file:///Users/MAC/SuneelWorkSpace/spine/state/CURRENT_STATE.json), [WORKSPACE_HEALTH.json](file:///Users/MAC/SuneelWorkSpace/spine/state/WORKSPACE_HEALTH.json), [system_profile.json](file:///Users/MAC/SuneelWorkSpace/spine/system-context/system_profile.json), [tool_inventory.json](file:///Users/MAC/SuneelWorkSpace/spine/tools/tool_inventory.json) |

### Nerve System
The nerve system is implemented via [nerve_propagator.py](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_propagator.py) and configured in the central [nerve_registry.json](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_registry.json). 
* **Registry**: Tracks each organ's metadata path, subscriber list (`notifies`), and `inbox` directory.
* **Propagation**: When `notify_change(organ, event_type, detail)` is called, a JSON payload is generated and written to the `inbox` folder of all subscriber organs (e.g. `heart/nerve_inbox/`). Events are durably logged to [nerve_events.jsonl](file:///Users/MAC/SuneelWorkSpace/blood/logs/nerve_events.jsonl).
* **Consuming**: Organs query their inboxes using `check_inbox(organ)` and prune them with `clear_inbox(organ)`.

---

## FOR AI AGENTS — BOOT SEQUENCE

Every agent session MUST start with this exact sequence:

1. Read `skeleton/rules/AGENT_SYSTEM.md`
2. Read `skeleton/rules/IDENTITY.md`
3. Read `skeleton/rules/SAFETY_BOUNDARIES.md`
4. Read `dna/identity/prompts/identity_prompt.md`
5. Read `dna/identity/profile/tone_profile.md`
6. Read `dna/identity/profile/decision_profile.md`
7. Read `brain/memory/SESSION_HANDOFF.md`
8. Read `spine/state/CURRENT_STATE.json`
9. Read `nervous/mcp/server/config/resource_map.json`
10. Run: `memory-search "current active goals and recent decisions" --k 10`

Confirm: ✅ Context, identity, memory, and capabilities loaded

---

## CONTROL CENTER (EYES)

Dashboard running at: http://localhost:7777
Start with: `workspace-dashboard`

### What It Does
Provides a centralized, real-time Web dashboard UI (built using HTML, static/style.css, static/dashboard.js, and a FastAPI/WebSocket server in `eyes/dashboard/server.py`) to manage and monitor SuneelWorkSpace. It tracks goals, agent activities, telemetry, model status, and the evolution engine status.

### 6-Stage Execution Pipeline
Designed for complex workflow runs, this pipeline monitors step-by-step progress via WebSockets:
1. **brainstorm** (🧠): Explores intent, extracts goals, and identifies parameters.
2. **plan** (📋): Builds a structured step-by-step action plan.
3. **confirm** (✋): Pauses for Suneel's visual approval (WebSocket confirm gate) if execution is CONTROLLED.
4. **implement** (⚙️): Dispatches commands and executes each action.
5. **test** (🧪): Runs tests to validate outputs.
6. **wire** (🔗): Commits changes, updates workspace state, and saves telemetry logs.

### API Routes
* `GET /`: Serves the dashboard HTML client.
* `GET /api/goals`: Retrieves goal status lists.
* `GET /api/agent`: Gets recent agent activity events.
* `GET /api/memory`: Views brain memory files.
* `GET /api/mcp`: Checks MCP server status.
* `GET /api/health`: Polls current workspace health.
* `GET /api/telemetry`: Fetches SQL telemetry metrics.
* `GET /api/history`: Returns execution logs.
* `GET /api/suggestions`: Polls anticipation suggestions.
* `GET /api/status`: General status summary.
* `GET /api/models/status`: Retrives model fallback quotas.
* `POST /api/approvals/approve`: Visual click to approve pending actions.
* `POST /api/approvals/reject`: Visual click to reject pending actions.
* `POST /api/health/repair`: Triggers 8-stage repair pipeline.
* `POST /api/lab/autolab/run`: Launches experiment loop.

### Quick Actions
* **Night Shift**: Triggers `dag-run orchestrator/dag/pipelines/night_shift.yaml` to run background maintenance.
* **Gap Scan**: Triggers `python3 evolution/gap_finder.py` to evaluate capability coverage.
* **Challenge Generation**: Triggers `python3 evolution/challenger.py` to compile optimization templates.
* **Screenshot**: Triggers `screenshot-take` to capture current dashboard state.
* **Model Health Check**: Triggers `model-health` to test provider latencies.
* **Evolution Cycle**: Triggers `python3 evolution/engine.py cycle` to run a gap and challenge evolution cycle.
* **Morning Brief**: Triggers `morning-brief` to fetch feeds and compile the daily briefing.
* **Workspace CI**: Triggers `workspace-ci` to execute the automated testing suite.

### Panels
* **Health & Repair**: Shows workspace health score, launchd status, and repair triggers.
* **Model Router**: Displays priority models, call limits, and error rates.
* **Goal Tracker**: Lists active and failed goals with progress bars.
* **Visual Approvals**: Shows pending execution requests requiring approval.
* **Evolution & Gaps**: Visualizes gaps found and queued self-challenge templates.

---

## AUTONOMOUS HEALTH REPAIR

Click 🔧 Repair to 98% in the dashboard health panel to trigger.
Or: POST http://localhost:7777/api/health/repair

### 8-Stage Repair Pipeline
Defined in [health_repair_pipeline.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/execution/health_repair_pipeline.py):
1. **Memory File Integrity**: Verifies critical markdown files (`MEMORY.md`, `DECISIONS.md`, `SESSION_HANDOFF.md`) and reconstructs them if deleted.
2. **Broken Symlink Scan**: Searches for broken links in core folders and logs warning reports.
3. **MCP Server Health**: Pings main.py with `--health-check` to test WebSocket/gateway.
4. **Vector Store Accessibility**: Verifies vector search DB is present on disk.
5. **Pipeline State Recovery**: Audits pipeline_state.json and recovers interrupted executions.
6. **JSON Config Validation**: Scans all folders for malformed JSON configs.
7. **Workspace Health Tools**: Runs CLI diagnostics `agent-doctor` and `agent-repair`.
8. **Score & Report**: Computes post-repair score (adding 3 points per fix) and saves run metrics to `blood/logs/repair_reports/`.

### Score-Aware Depth
Implemented in [health_repair_pipeline.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/execution/health_repair_pipeline.py), the `get_repair_depth(score)` function maps current health score to specific repair stages:
* **95%+** → **light** (runs Stage 3 and Stage 7 only)
* **80%+** → **standard** (runs Stages 1-4 and Stage 7)
* **60%+** → **deep** (runs all 8 stages)
* **<60%** → **full** (runs all 8 stages + full issue surfacing)

---

## AUTONOMOUS EVOLUTION ENGINE (LAB)

Driven by background engine loops scanning gaps and drafting hypotheses.

### Day Mode vs Night Mode
Configured dynamically via [evolution_config.json](file:///Users/MAC/SuneelWorkSpace/lab/evolution/evolution_config.json) and managed by [engine.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/engine.py):
* **Day Shift**: Runs one cycle every 45 minutes (customizable in config), scanning gaps and enqueuing challenger logs.
* **Night Shift (wraps midnight, customizable in config, e.g., 10 PM - 6 AM)**: Boosts cycle interval to run every 30 minutes, running backup/repair tools and enqueuing safe autolab experiments.

### Self-Challenge System
Defined in [challenger.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/challenger.py). It randomly compiles optimization templates across areas (performance, coverage, reliability, intelligence, automation, integration) and logs them to `lab/evolution/challenges.jsonl`.

### Gap Finder
Defined in [gap_finder.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/gap_finder.py). It checks the existence of 15 expected core capabilities and outputs status JSON reports to `brain/system/gap_analysis_latest.json`.

### Night Shift Pipeline
Configured in [night_shift.yaml](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/pipelines/night_shift.yaml), executing 15 steps:
1. `backup`: Runs `workspace-backup`
2. `model_health`: Pings model providers
3. `visual_screenshot`: Captures current dashboard view
4. `visual_repair`: Auto-heals visual bugs
5. `gap_scan`: Evaluates capability statuses
6. `challenge`: Compiles self-improvement templates
7. `hypothesis_generate`: Enqueues autolab hypotheses
8. `autolab_run`: Runs SAFE level experiments
9. `health_repair`: Runs 8-stage repair pipeline
10. `memory_reindex`: Reindexes vector Chroma DB
11. `graph_rebuild`: Builds obsidian markdown backlink map
12. `capability_update`: Refreshes gap statuses
13. `prompt_eval`: Runs evaluation scores on current prompts
14. `morning_brief`: Fetches feeds and compiles daily briefing digest
15. `workspace_ci`: Runs unit tests
16. `agent_finish`: Updates session logs and completes run

### Starting the Evolution Engine
```sh
evolution-start    # starts engine daemon (or in tmux session 'evolution-engine')
evolution-stop     # stops the engine
```

---

## MODEL ROUTER WITH AUTOMATIC FALLBACK (HEART)

Exposes smart provider fallbacks to avoid token limits or developer lockouts.

### Model Priority Order
Configured dynamically inside [model_registry.json](file:///Users/MAC/SuneelWorkSpace/heart/model_router/model_registry.json) and checked by [router.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/router.py):
1. `claude-sonnet-4-6` (Primary developer & analyst model, priority 1)
2. `claude-opus-4-8` (Heavy reasoning fallback, priority 2)
3. `gpt-4o` (General purpose agent fallback, priority 3)
4. `gemini-2.5-pro` (Long context fallback, priority 4)

### Quota Tracking
Persisted in [quota_state.json](file:///Users/MAC/SuneelWorkSpace/heart/model_router/quota_state.json) and tracked by [quota_tracker.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/quota_tracker.py). It records daily token usage and calls, resetting quotas automatically at midnight.

### Fallback Behavior
When `get_best_model(task_type, preferred)` is called, the router checks if the preferred model is marked `available: true`. If exhausted, it logs a fallback event to `heart/model_router/fallback_log.jsonl` and selects the next available model in the priority chain.

### Commands
```sh
model-status    # show all models with availability and token usage
model-health    # ping each model with test prompt
```

---

## VISUAL MONITOR SYSTEM (EYES)

Tracks visual state representation of the workspace.

### Screenshot Management
Screenshots are taken via [screenshot_manager.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/screenshot_manager.py) and stored as [dashboard-live.png](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/screenshots/dashboard-live.png) inside the dashboard static folder for real-time visual inspection.

### Visual Repair Agent
Implemented in [visual_repair_agent.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/visual_repair_agent.py). It processes screenshot comparisons and enqueues adjustments or automatically patches CSS files if styling mismatches are found.

### Vision Implementer
Implemented in [vision_implementer.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/vision_implementer.py), providing a translation layer to compile mocked screenshot designs directly into HTML/CSS files.

### Commands
```sh
screenshot-take     # take dashboard screenshot manually
visual-monitor      # start background screenshot daemon
visual-repair       # process visual repair queue
```

---

## WORLD MONITOR (EARS)

Scans external feeds and provides daily intelligence context.

### Sources
Configured in [monitor_config.json](file:///Users/MAC/SuneelWorkSpace/ears/monitor/config/monitor_config.json):
* GitHub releases and PRs of tracked repositories
* RSS news directories
* Arxiv academic publications

### Morning Brief
Generated daily by [digest_builder.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/digest/digest_builder.py) combining external news with active goal status reports, outputting the markdown file inside the workspace for daily briefing.

### Commands
```sh
monitor-run        # fetch from all sources
morning-brief      # build today's digest
```

---

## MEMORY SYSTEM (BRAIN)

Handles semantic query indexing and knowledge graphing.

### Semantic Search
Exposes vector search tools in [semantic_search.py](file:///Users/MAC/SuneelWorkSpace/brain/memory/vector/semantic_search.py) querying a local ChromaDB store directory to return context matches within memory.

### Memory Files
* [MEMORY.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/MEMORY.md): Permanent facts.
* [DECISIONS.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/DECISIONS.md): Architectural decisions.
* [SESSION_HANDOFF.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/SESSION_HANDOFF.md): Work session persistence.
* [NOTES.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/NOTES.md): Temp scratch note entries.

### Knowledge Graph
Built via [build_graph.py](file:///Users/MAC/SuneelWorkSpace/brain/graph/build_graph.py) (saving graph lists to `brain/graph/knowledge_graph.json`), allowing agents to crawl note relationships and isolate orphan pages (logged to [orphan_notes.md](file:///Users/MAC/SuneelWorkSpace/brain/graph/reports/orphan_notes.md)).

### Brain Context Injector
Defined in [context_injector.py](file:///Users/MAC/SuneelWorkSpace/brain/injector/context_injector.py) (and linked CLI `brain-inject`), resolving context dependencies by ranking notes based on a recency decay scoring algorithm.

### Commands
```sh
memory-search "query"    # semantic search across all memory
memory-reindex           # re-embed all memory files
brain-inject --task "..."  # inject relevant context before a task
brain-graph-build        # rebuild knowledge graph
brain-graph-query        # query the knowledge graph
brain-staleness          # find stale/orphan notes
```

---

## IDENTITY SYSTEM (DNA)

Specifies Suneel's identity profile, communication style, and adaptive learning loops.

### Voice and Tone
Tone parameters defined in [tone_profile.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/profile/tone_profile.md): casual, direct, smart, softened, structured, and CASUAL conversational.

### Decision Style
Configured in [decision_profile.md](file:///Users/MAC/SuneelWorkSpace/dna/identity/profile/decision_profile.md): leads with analysis, split uncertainty into subproblems, autopilot by default.

### Adaptive Identity
Adjusts profiles from feedback via [adaptive_identity.py](file:///Users/MAC/SuneelWorkSpace/dna/identity/adaptive/adaptive_identity.py). Takes input from `identity-accept`, `identity-reject`, and `identity-adjust` commands, applying weight parameters from [signal_weights.json](file:///Users/MAC/SuneelWorkSpace/dna/identity/adaptive/signal_weights.json) to prevent sudden stylistic drifts.

### Prompt Versioning
Stores incremental prompts under `dna/identity/prompts/versions/` and validates adjustments using the testing scripts in `dna/identity/prompts/eval/`.

### Commands
```sh
prompt-eval --version current    # score current prompt version
prompt-new                       # create new version
prompt-promote <version>         # promote after passing eval
prompt-rollback                  # revert to previous version
identity-accept <id>             # record accepted output
identity-reject <id> "reason"    # record rejected output
identity-adjust "instruction"    # manual adjustment
feedback-ingest                  # process feedback inbox
```

---

## TELEMETRY SYSTEM (BLOOD)

SQLite-driven query tracking and execution logging.

### Schema
Maintained inside [schema.sql](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/schema.sql) defining tables for `traces`, `metrics`, and `logs` to capture execution outcomes.

### Nested Traces
The trace system tracks execution hierarchy by linking parent and child operations through `trace_id` and `parent_trace_id` columns, persisted inside [telemetry.db](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry.db).

### Anomaly Detection
Implemented in [telemetry_anomaly.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_anomaly.py). Scans performance indices and flags latency regression or unexpected token consumption peaks.

### Commands
```sh
telemetry-query summary --days 7    # agent performance table
telemetry-anomalies                 # flag regressions
```

---

## AUTOLAB SYSTEM (LAB)

Safely performs self-evolution experiment runs.

### Experiment Lifecycle
Hypotheses are enqueued in `lab/autolab/experiment_queue.md`, run via [runner.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/runner.py), graded by [evaluator.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/evaluator.py), and promoted by [promotion_gate.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/promotion_gate.py) if baseline metrics improve; otherwise rolled back.

### Execution Levels
* **SAFE**: Commands with zero system mutation risks. Runs automatically.
* **CONTROLLED**: Moderate mutation risks. Requires manual approval click.
* **RESTRICTED**: High system risks. Banned from auto-runs; requires CLI escalation.

### Hypothesis Generator
Defined in [hypothesis_generator.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/hypothesis_generator.py), sourcing improvement ideas from error logs and capability gaps.

### Commands
```sh
autolab-run              # run queued experiments
autolab-status           # show experiment queue
autolab-promote          # promote successful experiment
hypothesis-generate      # generate new hypotheses
hypothesis-rank --top 5  # rank by priority
```

---

## NATURAL LANGUAGE DISPATCHER (MOUTH)

Processes user natural language commands.

### How It Works
Exposes dispatcher hooks via [ws.py](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/ws.py). Categorizes prompts against intents, filters confidence scores below thresholds, and allows dry-runs.

### Available Intents
Configured in [intent_map.json](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/intent_map.json):
* `status` -> `agent-status`
* `search_memory` -> `memory-search`
* `morning_brief` -> `morning-brief`
* `goals` -> `goal-status`
* `repair` -> `health-repair`

### Usage
```sh
ws "what's broken"                          # health check
ws "search memory for auth decisions"       # semantic search
ws "run morning brief"                      # world monitor digest
ws "what are my current goals"              # goal status
ws "any intent" --explain                   # show resolution details
ws "any intent" --dry-run                   # preview without executing
ws --list                                   # show all available intents
```

---

## WORKFLOW DAG COMPOSER (HANDS)

Orchestrates sequential task executions.

### Scheduled Pipelines
Pipelines defined under `heart/orchestrator/dag/pipelines/`:
* [system_health.yaml](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/pipelines/system_health.yaml): Scheduled daily at 2:00 AM. Runs audit, gaps, recommendations, and doctor.
* [idea_to_goal.yaml](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/pipelines/idea_to_goal.yaml): Manual trigger. Processes capture, research, goal creation, and planning.
* [morning_brief.yaml](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/pipelines/morning_brief.yaml): Scheduled daily at 7:00 AM. Fetches news, checks goals, queries telemetry, and builds brief.
* [night_shift.yaml](file:///Users/MAC/SuneelWorkSpace/heart/orchestrator/dag/pipelines/night_shift.yaml): Scheduled daily at 10:00 PM. Runs backups, screenshots, gaps, autolab loops, reindexing, and CI.

### Commands
```sh
dag-run <pipeline.yaml>                              # execute pipeline
dag-run <pipeline.yaml> --dry-run                    # preview
dag-validate <pipeline.yaml>                         # validate
```

---

## COMPLETE COMMAND REFERENCE

All executable commands reside inside `hands/bin/` as symlinks pointing to target organ implementations.

### 🧠 Brain Commands
* `memory-search` -> [semantic_search.py](file:///Users/MAC/SuneelWorkSpace/brain/memory/vector/semantic_search.py): Semantic query matches.
* `memory-reindex`: Reindexes vector embedding databases.
* `brain-inject` -> [context_injector.py](file:///Users/MAC/SuneelWorkSpace/brain/injector/context_injector.py): Injects context before runs.
* `brain-graph-build` -> [build_graph.py](file:///Users/MAC/SuneelWorkSpace/brain/graph/build_graph.py): Rebuilds backlink files.
* `brain-graph-query` -> [graph_query.py](file:///Users/MAC/SuneelWorkSpace/brain/graph/graph_query.py): Queries backlink nodes.
* `brain-staleness` -> [staleness_detector.py](file:///Users/MAC/SuneelWorkSpace/brain/injector/staleness_detector.py): Finds stale notes.

### 💓 Heart Commands
* `model-route` -> [router.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/router.py): Best model mapping resolver.
* `model-status`: Prints usage metrics and availabilities.
* `model-health` -> [health_checker.py](file:///Users/MAC/SuneelWorkSpace/heart/model_router/health_checker.py): Provider latency diagnostics.
* `goal-create`: Instantiates goal tracker.
* `goal-plan`: Resolves step dependencies.
* `goal-status`: Goal progress and queues.

### 👁️ Eyes Commands
* `workspace-dashboard` -> [dashboard_start.sh](file:///Users/MAC/SuneelWorkSpace/hands/scripts/dashboard_start.sh): Start Control Center server.
* `screenshot-take` -> [screenshot_manager.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/screenshot_manager.py): Visual capture helper.
* `visual-monitor`: Background screenshot loops.
* `visual-repair` -> [visual_repair_agent.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/visual_repair_agent.py): CSS/HTML repair pipeline.

### 👂 Ears Commands
* `monitor-run` -> [monitor_runner.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/monitor_runner.py): Fetch news/RSS.
* `morning-brief` -> [digest_builder.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/digest/digest_builder.py): Compile daily digest.

### 🫀 Nervous Commands
* `nerve-status` -> [nerve_status.py](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_status.py): Centralized registry status.
* `mcp-start`: Launches MCP server.
* `mcp-status`: Checks MCP gateway connectivity.
* `mcp-doctor`: Pings server health.
* `mcp-reindex`: Re-indexes MCP assets.

### 🩸 Blood Commands
* `telemetry-query` -> [telemetry_query.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_query.py): SQLite telemetry reporting.
* `telemetry-anomalies` -> [telemetry_anomaly.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_anomaly.py): Performance regression checks.

### 🤲 Hands Commands
* `agent-start`: marcar startup session checkpoints.
* `agent-finish`: Marks closeouts and logs.
* `agent-doctor`: Checks workspace health rules.
* `agent-repair`: Auto-heals symlinks and directories.
* `workspace-backup`: Packs tar snapshots of the workspace.
* `workspace-ci`: Runs automated unit testing suites.

### 👄 Mouth Commands
* `ws` -> [ws.py](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/ws.py): NL command routing.
* `mail-status`: outbound email status.
* `imessage-status`: iMessage permissions and delivery.

### 🧬 DNA Commands
* `prompt-eval`: Evaluates system prompts.
* `prompt-promote`: Commits prompt candidate changes.
* `identity-accept`: Learns stylistic accept patterns.
* `identity-reject`: Logs style rejection constraints.

### 🔬 Lab Commands
* `autolab-run` -> [runner.py](file:///Users/MAC/SuneelWorkSpace/lab/autolab/runner.py): Safe experiment loop.
* `autolab-status`: Lists autolab queues.
* `evolution-start` -> [engine.py](file:///Users/MAC/SuneelWorkSpace/lab/evolution/engine.py): Evolution engine daemon launch.

### 📋 Spine Commands
* `workspace-index`: Re-scans indexing patterns.
* `log-enhancement` -> [enhancement_logger.py](file:///Users/MAC/SuneelWorkSpace/spine/enhancement_logger.py): Logs updates to main enhancement indices.

---

## SAFETY MODEL

Enforced by [SAFETY_BOUNDARIES.md](file:///Users/MAC/SuneelWorkSpace/skeleton/rules/SAFETY_BOUNDARIES.md) and [BOUNDED_SELF_UPGRADE.md](file:///Users/MAC/SuneelWorkSpace/skeleton/rules/BOUNDED_SELF_UPGRADE.md).

### Execution Levels
* **SAFE**: Zero mutation risk (reads, status lookups). Auto-executes.
* **CONTROLLED**: Medium risk (code edit, goal plans). Pauses for dashboard visual approval.
* **RESTRICTED**: High risk (outbound messaging, package installs, deletions). Requires explicit CLI confirmation.

### What Is Never Auto-Executed
* Outbound iMessages or emails.
* Destructive filesystem deletes.
* Money/account modifications.
* Unverified package installations.

---

## HOW TO EXTEND THE SYSTEM

### Adding a New Capability
1. Identify target organ for placement.
2. Run `duplication-guard <path> --intent "description"` to ensure no overlap.
3. Write script/module files in target organ subdirectory.
4. Symlink entrypoint into [hands/bin/](file:///Users/MAC/SuneelWorkSpace/hands/bin/).
5. Register resource inside [resource_map.json](file:///Users/MAC/SuneelWorkSpace/nervous/mcp/server/config/resource_map.json).
6. Add intent mapping to [intent_map.json](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/intent_map.json).
7. Notify nervous subscribers: `python3 nervous/nerve_propagator.py notify <organ> "new_capability" <path>`
8. Validate health and re-index: `agent-doctor` and `mcp-reindex`.
9. Log update: `log-enhancement <organ> "Added new capability..."`

### Rules That Never Change
1. No root-level file clutter; all files belong inside their organ.
2. Log updates to the enhancement index.
3. Propagate changes via nervous system notifications.
4. Execute `duplication-guard` and `integrity-guard` before changes.

---

## CURRENT LIMITATIONS AND KNOWN GAPS

* **Outdated Diagnostic Tools**: Diagnostic scripts `agent-doctor` and `agent-repair` search for old `agent-system/` paths and do not recognize the new 12-organ layout, reporting incorrect misplaced file errors and lowering health score to "repairable" or "attention".
* **Manual Setup Symlink**: The global Claude config symlink `~/.claude/CLAUDE.md` -> `~/SuneelWorkSpace/CLAUDE.md` must still be configured manually in new host setups.

---

## ENHANCEMENT LOG

* 2026-06-26: Complete documentation update — README rewritten end-to-end based on full system scan, all 12 organ READMEs created, CLAUDE.md and AGENTS.md updated, nerve_registry.json verified
* 2026-06-26: Gap analysis and full repair — fixed all broken symlinks in hands/bin/, created dynamic evolution_config.json and model_registry.json, resolved paths and import errors, implemented get_repair_depth in health_repair_pipeline.py, and updated all documentation.
