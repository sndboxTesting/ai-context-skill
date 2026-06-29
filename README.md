# SuneelWorkSpace

> Living, self-maintaining AI engineering workspace on Apple M4 Max (64 GB RAM, macOS 15).  
> 12 organs. 194 CLI commands. 103/103 tests passing. Ollama running locally.

---

## Architecture — 12 Organs

| Organ | Path | Role |
|-------|------|------|
| 🧠 brain | `brain/` | Vector memory, anticipation engine, research, context injection |
| ❤️ heart | `heart/` | Task queues, goals, model router (5 models), model rotator |
| 👁️ eyes | `eyes/` | FastAPI dashboard (port 7777), 13 widgets, WebSocket execution streaming |
| 👂 ears | `ears/` | RSS/GitHub monitors, morning brief, personalized digest |
| ⚡ nervous | `nervous/` | Nerve propagator, nerve healer, MCP connectors, nerve registry |
| 🦴 skeleton | `skeleton/` | Agent rules, safety boundaries, shared instructions |
| 🩸 blood | `blood/` | Telemetry SQLite, all logs (JSONL), anomaly detection |
| 🤲 hands | `hands/` | 194 CLI symlinks in bin/, scripts/, night_shift.yaml DAG |
| 🗣️ mouth | `mouth/` | Intent dispatcher, mail, iMessage |
| 🧬 dna | `dna/` | Identity profiles, Hermes agent, Ollama Modelfile, training data |
| 🧪 lab | `lab/` | 9 Ollama engines, evolution, autolab experiments, self-evolution |
| 🫀 spine | `spine/` | Health state, workspace health JSON, diagnostics, audit, backups |

---

## Session Boot (Mandatory)

```
✅ Loading workspace shared brain
```

Read in order before meaningful work:

1. `skeleton/rules/AGENT_SYSTEM.md`
2. `skeleton/rules/IDENTITY.md`
3. `skeleton/rules/WORKFLOW_RULES.md`
4. `skeleton/rules/SAFETY_BOUNDARIES.md`
5. `skeleton/rules/STARTUP_CHECKLIST.md`
6. `brain/memory/MEMORY.md`
7. `brain/memory/DECISIONS.md`
8. `heart/tasks/ACTIVE_TASKS.md`
9. `brain/memory/SESSION_HANDOFF.md`
10. `spine/state/CURRENT_STATE.json`
11. `spine/state/WORKSPACE_HEALTH.json`

---

## Ollama Intelligence Stack

6 local models, 9 engines orchestrated every 5 minutes by `lab/autolab/ollama_orchestrator.py`:

| Engine | Model | Schedule | Purpose |
|--------|-------|----------|---------|
| ollama_repair | suneelworkspace | every 4h | Suggest SAFE workspace fixes |
| nerve_healer | suneelworkspace | every 6h | Heal broken organ connections |
| memory_curator | suneelworkspace | every 12h | Curate MEMORY.md, DECISIONS.md, PATTERNS.md |
| ollama_learn | llama3.1 | every 8h | Generate skills from experiments |
| code_review | codellama | every 6h | Review Python files for bugs/patterns |
| security_scan | mistral | every 12h | Detect secrets, unsafe patterns |
| experiment_skills | suneelworkspace | every 6h | Generate skill docs from experiments |
| suggestion_consumer | — | every 2h | Convert suggestions → TASK_QUEUE.md tasks |
| rebuild_context | — | weekly | Rebuild Modelfile from live workspace state |

**Context injection**: every engine gets 4,000 chars of live workspace context (identity + memory + tasks + handoff + decisions) via `lab/autolab/context_injector.py`.

**suneelworkspace model**: rebuilt from `dna/agents/hermes/ollama_models/Modelfile.workspace` — 9,553-char system prompt with Suneel's identity, all 12 organs, active tasks, decisions, and patterns baked in.

```bash
ollama-stack-start    # Start orchestrator + nerve healer in tmux
ollama-stack-status   # Check which engines are DUE vs IDLE
ollama-stack-stop     # Stop tmux sessions
rebuild-model         # Rebuild suneelworkspace Modelfile from live state
consume-suggestions   # Manually run suggestion→task converter
ollama-orchestrate    # Run orchestrator directly
```

---

## Test Suite

**103/103 tests passing** (0.4s)

```bash
run-tests       # Run full suite (pytest + JUnit XML + JSON report)
repair-loop     # Autonomous repair: Ollama analyzes failures, applies SAFE fixes, retries
readme-sync     # Sync all READMEs with latest test results
```

Tests live in `tests/` — organized by organ, integration, Ollama engines, nerve system, security, performance. Reports saved to `tests/reports/`.

**Pre-commit hook**: `codellama` reviews staged Python diffs on every `git commit` (warn-only, never blocks). Install with `install-git-hooks`.

---

## Dashboard

FastAPI server at `http://localhost:7777`. WebSocket-streamed 6-stage execution pipeline (brainstorm → plan → confirm → implement → test → wire).

```bash
workspace-dashboard   # Start dashboard
```

**13 widgets**: Goals, Agent Activity, Memory Health, MCP Status, Anticipation, Autolab, README Health, Model Status, Evolution, Visual Monitor, Approval Queue, Ollama, Hermes, Nerve System, Test Suite.

**Quick actions**: Night Shift, Gap Scan, Challenge, Screenshot, Models, Evolution, Morning Brief, CI.

---

## Essential CLI

```bash
# Agent lifecycle
agent-start            # Start session, load context
agent-finish "summary" # Close session, update handoffs
agent-doctor           # Diagnose workspace health
workspace-context      # Print current state brief

# Memory & knowledge
memory-search "query"  # Semantic vector search
memory-curate          # Ollama memory curation pass
morning-brief          # Build personalized daily digest
morning-brief-personal # Personalized brief with Ollama scoring

# Goals & tasks
goal-create            # Create a new goal
goal-status            # View active goals
goal-execute           # Execute a goal step

# Model routing
model-route            # Route task to best model
model-health           # Check model availability
model-rotate           # Get best model for task type

# Nerve system
nerve-heal             # Heal broken organ connections
nerve-status           # View all 12 organ statuses

# Ollama engines
ollama-repair          # Run repair engine directly
ollama-review          # Run code review
security-scan          # Run security scanner
memory-curate          # Run memory curator
experiment-skills      # Generate skills from experiments

# Night automation
night-shift (dag-run)  # Run full nightly pipeline
```

---

## Nerve System

All inter-organ events flow through `nervous/nerve_propagator.py`:

```python
from nervous.nerve_propagator import notify_change, get_status
notify_change("brain", "memory_updated", "brain/memory/MEMORY.md")
status = get_status()  # Returns health dict for all 12 organs
```

Every organ has `nerve.json` (v1.1) with `provides`, `needs`, `key_files`, `cli_commands`. Healed automatically by `nervous/nerve_healer.py`.

---

## Safety Boundaries

- Never delete important files without explicit approval
- Never touch billing or account settings
- Never send outbound comms (mail, iMessage) without approval
- Autopilot for SAFE actions; ask for CONTROLLED or HUMAN_REQUIRED
- All destructive fixes queued to `blood/logs/*_controlled_queue.json` for human review

---

## Key Files

| File | Purpose |
|------|---------|
| `skeleton/rules/AGENT_SYSTEM.md` | Canonical agent operating rules |
| `skeleton/rules/SAFETY_BOUNDARIES.md` | What agents must never do |
| `brain/memory/MEMORY.md` | Durable workspace facts |
| `brain/memory/DECISIONS.md` | Key decisions and reasons |
| `brain/memory/SESSION_HANDOFF.md` | Latest session summary |
| `spine/state/CURRENT_STATE.json` | Live workspace state |
| `spine/state/WORKSPACE_HEALTH.json` | Health score and issues |
| `heart/tasks/ACTIVE_TASKS.md` | Current task list |
| `dna/identity/profile/identity_profile.md` | Suneel's voice and style |
| `lab/autolab/ollama_orchestrator.py` | Engine scheduler |
| `lab/autolab/context_injector.py` | Workspace context for Ollama |
| `dna/agents/hermes/ollama_models/Modelfile.workspace` | Suneelworkspace model definition |
| `nervous/nerve_propagator.py` | Inter-organ event bus |
| `hands/automation/dag/pipelines/night_shift.yaml` | Nightly automation pipeline |

---

## Current Health

- **Health score**: see `spine/state/WORKSPACE_HEALTH.json`
- **Tests**: 103/103 passing
- **Ollama**: running — 6 models, 9 engines
- **Dashboard**: `http://localhost:7777`
- **Nerve system**: 12/12 organs connected (v1.1)
- **Pre-commit hook**: installed (codellama, warn-only)

*Last updated: 2026-06-28*
