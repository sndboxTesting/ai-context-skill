# lab

9 Ollama engines, autolab experiment framework, self-evolution cycle, and skill generation.

## What It Does

- **9 Ollama engines** — orchestrated every 5 min, each with its own model, schedule, and purpose
- **Context injector** — injects 4,000 chars of live workspace context into every engine call (5-min TTL cache)
- **Suggestion consumer** — converts SAFE high-confidence suggestions into `heart/tasks/TASK_QUEUE.md` tasks
- **Autolab** — experiment runner, hypothesis generator, skill extractor
- **Evolution** — `lab/evolution/` self-evaluates and proposes workspace improvements

## Autolab Engines

All in `lab/autolab/`, orchestrated by `ollama_orchestrator.py`:

| Engine | File | Model | Schedule |
|--------|------|-------|----------|
| Orchestrator | `ollama_orchestrator.py` | — | every 5 min (scheduler loop) |
| Repair | `ollama_repair_engine.py` | suneelworkspace | every 4h |
| Nerve Healer | `nervous/nerve_healer.py` (link) | suneelworkspace | every 6h |
| Memory Curator | `brain/memory/memory_curator.py` (link) | suneelworkspace | every 12h |
| Learning | `ollama_learn_engine.py` | llama3.1 | every 8h |
| Code Review | `code_review_engine.py` | codellama | every 6h |
| Security Scan | `security_scanner.py` | mistral | every 12h |
| Experiment Skills | `experiment_skill_generator.py` | suneelworkspace | every 6h |
| Suggestion Consumer | `suggestion_consumer.py` | — | every 2h |
| Model Rebuild | (via build_modelfile.py link) | — | weekly |

## Context Injector

`lab/autolab/context_injector.py`:

```python
from lab.autolab.context_injector import ask_ollama_with_context, build_context

# Ask with full workspace context as system prompt (4,000 chars, 5-min TTL cache)
response = ask_ollama_with_context(
    prompt="What should I fix next?",
    model="suneelworkspace",
    task_type="repair",      # or "general", "review", "security"
    timeout=120,
    temperature=0.2,
    num_ctx=8192
)
```

Context loaded: identity_profile.md, tone_profile.md, WORKSPACE_HEALTH.json, MEMORY.md, ACTIVE_TASKS.md, SESSION_HANDOFF.md, DECISIONS.md, PATTERNS.md.

## Suggestion Consumer

`lab/autolab/suggestion_consumer.py` — closes the Ollama output→action loop:

- Reads `blood/logs/ollama_suggestions.md` + `blood/logs/code_review_report.md`
- **SAFE + confidence ≥ 0.75** → appended to `heart/tasks/TASK_QUEUE.md` as actionable tasks
- **Below threshold** → queued to `blood/logs/suggestion_controlled_queue.json` for human review
- Runs every 2h via orchestrator. Manual: `consume-suggestions`

## Security Constraints

- All LLM-provided file paths validated by `_path_within_workspace()` before any write
  - Rejects: absolute paths, `..` segments, NUL bytes, paths outside WORKSPACE
- `create_file` restricted to `_ALLOWED_CREATE_DIRS = ("tests/", "blood/logs/", "lab/autolab/experiments/")`
- `fix_symlink` NEVER auto-applied — always queued to controlled queue
- Confidence below 0.75 → controlled queue, never auto-applied

## Evolution

`lab/evolution/` — self-evaluation and improvement proposals:
- Scores workspace health trends over time
- Proposes safe improvements to orchestrator engine configs
- Records decisions in `brain/memory/DECISIONS.md`

## CLI Commands

```bash
ollama-stack-start       # Start orchestrator + healer in tmux
ollama-stack-status      # Check engine DUE / IDLE status
ollama-stack-stop        # Stop tmux sessions
ollama-orchestrate       # Run one orchestrator pass directly
ollama-repair            # Run repair engine
ollama-review            # Run code review
ollama-learn             # Run learning engine
security-scan            # Run security scanner (mistral)
consume-suggestions      # Run suggestion→task converter
experiment-skills        # Extract skills from experiments
rebuild-model            # Rebuild suneelworkspace Modelfile
build-training-data      # Extract 103 training pairs from history
```

## Tests

Covered by `tests/ollama_engines/test_ollama_engines.py` — part of the 103/103 passing suite.

Key assertions: orchestrator imports correctly, context_injector caches within TTL, suggestion_consumer applies confidence threshold.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("lab", "engine_run_complete", "lab/autolab/ollama_orchestrator.py")
notify_change("lab", "suggestion_consumed", "blood/logs/ollama_suggestions.md")
notify_change("lab", "evolution_proposed", "lab/evolution/")
```

*Updated: 2026-06-28*
