# hands

194 CLI symlinks, 50+ scripts, launchd automation, and the night shift DAG pipeline.

## What It Does

- **CLI interface** — `hands/bin/` holds 194 symlinks (every workspace command)
- **Scripts** — `hands/scripts/` holds the actual implementations (50+ scripts)
- **Night shift DAG** — `hands/automation/dag/pipelines/night_shift.yaml` — nightly pipeline
- **Launchd plists** — `hands/automation/plists/` for scheduled macOS background jobs
- **Git hooks** — `hands/scripts/pre_commit_hook.sh` (codellama code review on commit)
- **Codex integration** — `hands/codex/` for Codex CLI project configs

## The Symlink Rule

**Every command in `hands/bin/` must be a symlink** — never a plain file or copy. Enforced by `tests/organs/hands/test_hands.py` (`os.path.islink()` checked for every entry).

```bash
# Add a new CLI command (always symlink)
ln -sf "$WORKSPACE/hands/scripts/my_script.sh" "$WORKSPACE/hands/bin/my-command"
```

## Key CLI Commands

### Agent Lifecycle
```bash
agent-start              # Load startup context, print workspace brief
agent-finish "summary"   # Close session, update handoffs, log session
agent-doctor             # Diagnose workspace health (all organs)
workspace-context        # Print current state JSON
workspace-dashboard      # Start FastAPI dashboard at port 7777
```

### Testing & CI
```bash
run-tests                # Run 103-test pytest suite → JUnit XML → JSON report
repair-loop              # Autonomous repair: Ollama analyzes failures, retries up to 5x
readme-sync              # Sync all READMEs with latest test results
install-git-hooks        # Install codellama pre-commit hook into .git/hooks/
```

### Memory & Knowledge
```bash
memory-search "q"        # Semantic vector search over brain/memory/
memory-curate            # Ollama memory curation pass
memory-reindex           # Rebuild ChromaDB vector index
morning-brief            # Build daily digest
morning-brief-personal   # Personalized Ollama-scored brief
```

### Ollama Stack
```bash
ollama-stack-start       # Start orchestrator + nerve healer in tmux sessions
ollama-stack-status      # Check engine DUE vs IDLE status
ollama-stack-stop        # Stop tmux sessions
ollama-orchestrate       # Run orchestrator directly (one scheduling pass)
ollama-repair            # Run repair engine
ollama-review            # Run code review engine
ollama-learn             # Run learning engine
security-scan            # Run security scanner (mistral model)
rebuild-model            # Rebuild suneelworkspace Modelfile from live state
consume-suggestions      # Run suggestion→task converter
build-training-data      # Extract 103 training pairs from workspace history
```

### Goals & Tasks
```bash
goal-create              # Create a goal
goal-status              # View active goals
goal-execute             # Execute a goal step
goal-complete            # Mark goal complete
goal-monitor             # Monitor goal progress
```

### Nerve System
```bash
nerve-heal               # Run Ollama nerve healer
nerve-status             # Print all 12 organ statuses
nerve-check              # Quick nerve.json validation
```

### Model Routing
```bash
model-route              # Route task to best model
model-health             # Check model availability
model-rotate             # Get best model for task type
model-status             # View rotation stats + quota
```

## Night Shift Pipeline

`hands/automation/dag/pipelines/night_shift.yaml` — nightly automated pipeline:

```yaml
steps:
  - memory_curate        # Curate MEMORY.md
  - brain_synthesize     # Synthesize context
  - ollama_learn         # Generate skills from experiments
  - hermes_telegram_brief  # Morning brief
  - run_tests            # Full pytest suite
  - repair_loop          # Autonomous repair (only if TEST_FAILURES > 0)
  - readme_sync          # Sync all READMEs
```

## Git Pre-Commit Hook

`hands/scripts/pre_commit_hook.sh`:
- Runs on every `git commit`
- Captures staged Python diff (`git diff --cached -- *.py`)
- Sends to `codellama` via Ollama API (warn-only, commit is never blocked)
- Logs result to `blood/logs/pre_commit_review.jsonl`
- **Security**: all dynamic values passed via `sys.argv` — zero shell variable interpolation into code strings

Install with: `install-git-hooks`

## Tests

Covered by `tests/organs/hands/test_hands.py` — part of the 103/103 passing suite.

Key assertions: every entry in `hands/bin/` is a symlink; key scripts exist in `hands/scripts/`.

*Updated: 2026-06-28*
