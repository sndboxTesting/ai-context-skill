# tests

103/103 tests passing. Autonomous repair loop. README sync. Full Ollama-powered CI.

## Status

```
✅ 103/103 PASSING (0.4s)
```

## Running Tests

```bash
run-tests       # Full suite: pytest + JUnit XML + JSON report saved to tests/reports/
repair-loop     # Autonomous repair: Ollama analyzes failures, applies SAFE fixes, retries up to 5x
readme-sync     # Sync all READMEs with latest test results
```

## Test Structure

```
tests/
  conftest.py                          # Shared fixtures (WORKSPACE constant, organ paths)
  test_runner.py                       # Master pytest runner (generates JUnit XML + JSON reports)
  autonomous_repair_loop.py            # Ollama-powered repair loop
  readme_sync.py                       # README test status updater
  reports/                             # JSON test reports (latest + history)
  organs/
    brain/test_brain.py                # Memory, vector search, anticipation, curator
    heart/test_heart.py                # Router, rotator, quota, goals
    eyes/test_eyes.py                  # Dashboard routes, widgets, WebSocket
    ears/test_ears.py                  # Monitors, digest builder, brief
    mouth/test_mouth.py                # Intent dispatcher, comms adapters
    hands/test_hands.py                # Symlink integrity (all 194 bin/ entries)
    blood/test_blood.py                # Log files, telemetry, anomaly detector
    dna/test_dna.py                    # Identity profiles, Modelfile, training data
    spine/test_spine.py                # Health state, diagnostics
  integration/
    test_integration.py                # Cross-organ flows (nerve events, suggestion→task)
  nerve_system/
    test_nervous.py                    # nerve_propagator, nerve_healer, nerve_registry
  ollama_engines/
    test_ollama_engines.py             # Orchestrator, context_injector, repair engine
  security/
    test_security.py                   # Path traversal, injection, input validation
  performance/
    test_performance.py                # Import times, file count thresholds
```

## Autonomous Repair Loop

`tests/autonomous_repair_loop.py` — closes the test failure → fix → verify cycle:

1. Run test suite via `test_runner.py`
2. Parse failures from JUnit XML (using `defusedxml`, not stdlib ET)
3. Send failure context to `suneelworkspace` Ollama model via context_injector
4. Parse SAFE suggestions from response
5. Validate all LLM-provided file paths with `_path_within_workspace()`
6. Apply SAFE fixes (`append_to_file`, `create_file` to allowed dirs only)
7. Queue `fix_symlink` to `blood/logs/repair_loop_controlled_queue.json` — NEVER auto-apply
8. Re-run tests; repeat up to 5 iterations or until ≥95% pass

**Security constraints**:
- `_path_within_workspace(path)`: rejects absolute paths, `..`, NUL bytes, paths outside WORKSPACE
- `create_file`: restricted to `_ALLOWED_CREATE_DIRS = ("tests/", "blood/logs/", "lab/autolab/experiments/")`
- `fix_symlink`: ALWAYS queued, never auto-applied

## Reports

After each run, saved to `tests/reports/`:
- `latest.json` — most recent run (pass/fail counts, failures list, duration)
- `run_YYYYMMDD_HHMMSS.json` — historical run archive

Readable by the dashboard (`/api/tests/status`) and README sync script.

## README Sync

`tests/readme_sync.py` reads `tests/reports/latest.json` and updates:
- Root `README.md` — test count and pass rate
- Organ READMEs — test file references and current status

## Pre-Commit Hook Integration

`hands/scripts/pre_commit_hook.sh` runs `codellama` on every `git commit`:
- Captures staged Python diff (`git diff --cached -- *.py`)
- Sends to codellama (warn-only, commit is never blocked)
- Logs to `blood/logs/pre_commit_review.jsonl`
- Install: `install-git-hooks`

## Night Shift Integration

Tests are part of the nightly `night_shift.yaml` DAG:
```yaml
- name: run_tests        # Full suite
  depends_on: ollama_learn
- name: repair_loop      # Autonomous repair (only if TEST_FAILURES > 0)
  depends_on: run_tests
- name: readme_sync      # Update READMEs
  depends_on: run_tests
```

*Updated: 2026-06-28*
