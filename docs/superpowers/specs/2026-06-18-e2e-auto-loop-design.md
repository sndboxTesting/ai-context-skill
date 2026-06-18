# E2E Auto Loop — Design Spec
*Date: 2026-06-18 | Status: Approved*

---

## Goal

Build a Home Assistant phone button that starts a safe, bounded end-to-end NLU eval → analyze failures → fix issues → retest loop on the Mac. Stop when combined eval ≥ 98.0% or when a safety/iteration limit is reached.

---

## Architecture

```
iPhone HA button
  → POST http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop  (n8n webhook)
  → n8n injects X-Adwi-Secret from $env.ADWI_LOCAL_SECRET
  → GET http://host.docker.internal:5055/adwi-e2e-auto-loop-start
  → server.py: Popen(e2e_auto_loop.py, detached) → returns JSON in <1s
  → background: e2e_auto_loop.py runs cycles, writes status.json + reports
  → (optional) iPhone push notification when done via HA notify
```

**Key constraint:** `server.py` uses `subprocess.run()` (blocking). The start route uses `subprocess.Popen(start_new_session=True)` instead so the phone button returns immediately. All other routes (status, report, cancel) keep the existing `subprocess.run` pattern and only read safe files.

---

## Files Changed / Created

| File | Change type | Description |
|------|-------------|-------------|
| `adwi/e2e_auto_loop.py` | New | Core loop engine — standalone, no adwi_cli imports |
| `adwi/adwi_cli.py` | Edit | Add 4 cmd_* functions + dispatch lines + help text |
| `adwi/services/command-api/server.py` | Edit | Add 3 read-only routes + 1 Popen start handler |
| `adwi/infra/docker/homeassistant-data/configuration.yaml` | Edit | Add adwi_e2e_auto_loop rest_command |
| `adwi/infra/docker/homeassistant-data/ui-lovelace.yaml` | Edit | Add 2 buttons to existing grid |
| `adwi/automation/workflows/adwi-e2e-auto-loop.json` | New | Importable n8n workflow template |
| `adwi/docs/E2E_AUTO_LOOP.md` | New | User-facing documentation |

**New directory:** `adwi/notes/e2e-auto-loop/` — status.json, running.pid, per-job subdirs

---

## `e2e_auto_loop.py` — Core Loop Engine

### Single-instance enforcement
- Lock file: `adwi/notes/e2e-auto-loop/running.pid`
- On start: check if PID in lockfile is still alive. If alive → exit with error. If stale → overwrite.
- On exit (success, failure, cancel): remove lockfile.

### Entry point
```
main(target=98.0, max_cycles=3, dry_run=False, job_id=None, workers=5)
```

### Per-cycle flow

```
1. Preflight
   - py_compile all patchable Python files
   - run test_nlu_regex.py (unittest)
   - if either fails → abort cycle, write error to status, stop loop

2. Eval P1
   - subprocess.run([python3, run_large_eval.py, --workers, 5], timeout=2400s)
   - parse SESSION_DIR/results.jsonl → P1 pass rate

3. Eval P2
   - subprocess.run([python3, run_large_eval_p2.py, --workers, 5], timeout=1200s)
   - parse results.jsonl → P2 pass rate

4. Compute combined pass rate (dedup logic same as generate_master_report.py)

5. Check stop conditions
   - combined >= target → write success report, exit 0
   - max_cycles reached → write max-cycles report, exit 0

6. Analyze failures (Hybrid Option C)
   Phase A — Regex fixes:
     - Cluster failures by intent
     - Look up fix in KNOWN_REGEX_FIXES dict (pre-defined safe patterns)
     - For each applicable fix:
       a. Snapshot file
       b. Apply minimal patch
       c. py_compile
       d. run test_nlu_regex.py
       e. If tests regress → rollback, log skip
       f. Record patch in cycle report
   Phase B — LLM-needs report:
     - After all regex fixes applied (or none applicable):
     - If still below target: write "needs_llm_review": true in status.json
     - List unfixed failure clusters for human review
     - Do NOT invoke aider/Ollama autonomously

7. Update status.json with cycle summary

8. Check cancel file: adwi/notes/e2e-auto-loop/cancel
   If exists → remove it, write cancelled status, exit

9. Next cycle
```

### Dry-run mode
- Runs preflight only (steps 1 only), no eval, no patches
- Writes a dry-run report to the job dir
- Returns after 1 cycle regardless of target

### Status file schema
```json
{
  "job_id": "e2e-20260618-103000",
  "status": "running|success|failed|cancelled|needs_llm_review",
  "started_at": "2026-06-18T10:30:00",
  "updated_at": "2026-06-18T11:05:00",
  "target": 98.0,
  "max_cycles": 3,
  "cycle": 2,
  "cycles": [
    {
      "cycle": 1,
      "p1_pct": 95.7,
      "p2_pct": 97.0,
      "combined_pct": 95.8,
      "patches_applied": ["FIX-CHAT-001"],
      "patches_skipped": [],
      "duration_s": 2100
    }
  ],
  "final_combined_pct": null,
  "stop_reason": null,
  "needs_llm_review": false,
  "unfixed_clusters": [],
  "report_path": "adwi/notes/e2e-auto-loop/e2e-20260618-103000/"
}
```

---

## `server.py` Changes

### Start route (special Popen handler)
```python
if self.path == "/adwi-e2e-auto-loop-start":
    # Check not already running (read PID file)
    ...
    job_id = f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    log_path = E2E_LOOP_DIR / job_id / "loop.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [VENV_PY, E2E_LOOP_PY, "--job-id", job_id],
        start_new_session=True,
        stdout=open(log_path, "w"),
        stderr=subprocess.STDOUT,
        env={**os.environ, ...}
    )
    (E2E_LOOP_DIR / "running.pid").write_text(str(proc.pid))
    self._send_json(200, {"job_id": job_id, "status": "started", "pid": proc.pid})
    return
```

### Read-only routes (existing subprocess.run pattern)
```python
"/adwi-e2e-auto-loop-status": [VENV_PY, E2E_STATUS_READER, "--status"],
"/adwi-e2e-auto-loop-report": [VENV_PY, E2E_STATUS_READER, "--report"],
"/adwi-e2e-auto-loop-cancel": [VENV_PY, E2E_STATUS_READER, "--cancel"],
```

`E2E_STATUS_READER` is a tiny helper script that reads `status.json` / latest report and prints JSON. This keeps server.py clean and avoids any shell execution.

---

## Safe Command API Routes

| Route | Method | Action |
|-------|--------|--------|
| `GET /adwi-e2e-auto-loop-start` | Special Popen | Launch background job, return job_id |
| `GET /adwi-e2e-auto-loop-status` | subprocess.run | Read status.json, return JSON |
| `GET /adwi-e2e-auto-loop-report` | subprocess.run | Read latest cycle report, return JSON |
| `GET /adwi-e2e-auto-loop-cancel` | subprocess.run | Write cancel sentinel file, return ack |

Auth: existing `X-Adwi-Secret` header — unchanged.

---

## CLI Commands

| Command | Function | Description |
|---------|----------|-------------|
| `/e2e-auto-loop` | `cmd_e2e_auto_loop()` | Start loop (default: target=98, max-cycles=3) |
| `/e2e-auto-loop --target 98 --max-cycles 3` | same | Override defaults |
| `/e2e-auto-loop --dry-run` | same | Preflight only, no eval |
| `/e2e-auto-loop-status` | `cmd_e2e_auto_loop_status()` | Show current status |
| `/e2e-auto-loop-report` | `cmd_e2e_auto_loop_report()` | Show latest cycle report |
| `/e2e-auto-loop-cancel` | `cmd_e2e_auto_loop_cancel()` | Cancel running job |

All CLI commands call into `e2e_auto_loop.py` functions directly (not via subprocess).

---

## Home Assistant

### configuration.yaml addition
```yaml
rest_command:
  adwi_e2e_auto_loop:
    url: "http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop"
    method: POST
    content_type: "application/json"
    payload: '{"command": "e2e-auto-loop"}'
  adwi_e2e_auto_loop_status:
    url: "http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop-status"
    method: POST
    content_type: "application/json"
    payload: '{"command": "e2e-auto-loop-status"}'
```

### ui-lovelace.yaml addition (2 buttons in existing grid)
```yaml
- type: button
  name: E2E Auto Loop
  icon: mdi:refresh-auto
  tap_action:
    action: call-service
    service: rest_command.adwi_e2e_auto_loop
  hold_action:
    action: call-service
    service: notify.mobile_app_the_suns_iphone
    service_data:
      title: "Adwi E2E Loop"
      message: "E2E Auto Loop started"

- type: button
  name: E2E Loop Status
  icon: mdi:chart-line
  tap_action:
    action: call-service
    service: rest_command.adwi_e2e_auto_loop_status
```

No secrets in HA YAML. Secret stays in n8n env var only.

---

## n8n Workflow (`adwi-e2e-auto-loop.json`)

Nodes:
1. **Webhook trigger** — `POST /webhook/adwi-e2e-auto-loop`
2. **HTTP Request** — `GET http://host.docker.internal:5055/adwi-e2e-auto-loop-start`, header `X-Adwi-Secret: {{$env.ADWI_LOCAL_SECRET}}`
3. **Parse result** — JS code node extracts job_id, status from envelope
4. **HA Notify** (optional) — POST to HA webhook to send iPhone push "E2E loop started — job {job_id}"

Secret never logged. `active: false` (user imports and activates manually).

A second workflow template for `/adwi-e2e-auto-loop-status` follows identical pattern.

---

## Auto-Fix Safety Model (Hybrid Option C)

### Phase A — Regex fixes only (autonomous)
Allowed patchable files:
- `adwi/adwi_cli.py` (NLU regex + _INTENT_SYSTEM only)
- `adwi/logs/simeval/run_large_eval.py`
- `adwi/logs/simeval/run_large_eval_p2.py`
- `adwi/capabilities.json`
- docs under `adwi/docs/`

Never touched autonomously:
- `adwi/path_validator.py`
- `adwi/reason_engine.py`
- `adwi/backup.py`
- `adwi/services/command-api/server.py`
- Gmail/auth/secrets files

Fix protocol per patch:
1. Snapshot file to job dir
2. Apply minimal patch
3. `py_compile` check
4. Run `test_nlu_regex.py`
5. If regression → rollback from snapshot
6. Record outcome in cycle report

### Phase B — LLM review report (no autonomous action)
If target not met after Phase A:
- Set `needs_llm_review: true` in status.json
- List unfixed failure clusters with examples
- Stop — human reviews the report, applies LLM-assisted fixes manually

---

## Stop Conditions

| Condition | Action |
|-----------|--------|
| combined ≥ target (98.0%) | Write success report, exit 0 |
| max_cycles reached | Write max-cycles report, exit 0 |
| rollback failure | Write error report, exit 1 |
| safety-boundary file in patch target | Write safety-abort report, exit 1 |
| test regression after patch (rollback ok) | Skip that patch, continue |
| Ollama unreachable | Write no-ollama report, exit 1 |
| cancel file exists | Write cancelled report, exit 0 |

---

## Report Locations

```
adwi/notes/e2e-auto-loop/
├── status.json                      ← live status (always current)
├── running.pid                      ← lockfile (present only when running)
├── cancel                           ← sentinel: create to cancel
└── e2e-20260618-103000/
    ├── loop.log                     ← stdout/stderr from the background process
    ├── cycle-1-report.json          ← per-cycle detail
    ├── cycle-2-report.json
    ├── final-report.json            ← summary when loop ends
    └── snapshots/                   ← file snapshots before patches
        └── adwi_cli.py.bak
```

---

## Tests / Checks to Run After Implementation

```bash
python3 -m py_compile adwi/e2e_auto_loop.py
python3 -m py_compile adwi/services/command-api/server.py
python3 -m py_compile adwi/adwi_cli.py
python3 -m unittest adwi/simlab/tests/test_nlu_regex.py
python3 adwi/adwi_cli.py /e2e-auto-loop-status
python3 adwi/adwi_cli.py /e2e-auto-loop --target 98 --max-cycles 1 --dry-run
```

---

## Safety Invariants Preserved

- `X-Adwi-Secret` auth unchanged
- No arbitrary shell execution added to Safe Command API
- No secrets in HA YAML (only in n8n env var)
- No auto-commit, auto-push, or remote changes
- No Cloudflare Tunnel
- No weakening of PathValidator or BLOCKED_PATHS
- Max cycles default 3, timeout per eval subprocess, timeout per overall job
- cancel sentinel file requires no special privilege — any process can create it
