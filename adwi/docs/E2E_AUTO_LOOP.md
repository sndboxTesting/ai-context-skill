# E2E Auto Loop

Bounded NLU eval → analyze → fix → retest loop triggered from a Home Assistant phone button or CLI. Stops automatically at ≥98% combined pass rate or when a safety/iteration limit is reached.

---

## Architecture

```
iPhone HA button
  → tap "E2E Auto Loop"
  → POST http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop  (n8n)
  → n8n injects X-Adwi-Secret from $env.ADWI_LOCAL_SECRET
  → GET http://host.docker.internal:5055/adwi-e2e-auto-loop-start
  → server.py: Popen(e2e_auto_loop.py, start_new_session=True) → returns {job_id, status} in <1s
  → background process: adwi/e2e_auto_loop.py runs cycles
  → status/reports written to adwi/notes/e2e-auto-loop/
  → (optional) iPhone push when loop starts, via HA hold_action
```

Direct CLI (no phone required):
```bash
python3 adwi/adwi_cli.py /e2e-auto-loop
python3 adwi/adwi_cli.py /e2e-auto-loop --dry-run
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/e2e-auto-loop` | Start full loop (target=98%, max-cycles=3, foreground) |
| `/e2e-auto-loop --target 98 --max-cycles 3` | Override defaults |
| `/e2e-auto-loop --dry-run` | Preflight only — no eval, no patches (safe test) |
| `/e2e-auto-loop --analyze-only` | Run evals + write enriched failure reports; no patching |
| `/e2e-auto-loop --background` | Detach to background, return immediately |
| `/e2e-auto-loop-status` | Show current/last job status |
| `/e2e-auto-loop-report` | Show latest cycle or final report |
| `/e2e-auto-loop-cancel` | Cancel a running loop job |

**Recommended first-run workflow:**
```
1. /e2e-auto-loop --dry-run            # confirm preflight passes
2. /e2e-auto-loop --analyze-only       # run evals, no patches; review failure_clusters
3. (add entries to KNOWN_REGEX_FIXES in e2e_auto_loop.py after reviewing report)
4. /e2e-auto-loop --max-cycles 1       # single patch cycle
```

---

## Safe Command API Routes

Base URL: `http://127.0.0.1:5055` (LAN only — never exposed publicly)

| Route | Method | Returns |
|-------|--------|---------|
| `GET /adwi-e2e-auto-loop-start` | Popen (non-blocking) | `{job_id, status, pid}` in <1s |
| `GET /adwi-e2e-auto-loop-status` | subprocess.run | Contents of `status.json` |
| `GET /adwi-e2e-auto-loop-report` | subprocess.run | Latest cycle or final report JSON |
| `GET /adwi-e2e-auto-loop-cancel` | subprocess.run | `{ok: true, cancel_requested: true}` |

All routes require `X-Adwi-Secret` header. Secret stored in `adwi/config/.env` (gitignored).

---

## Lock Ownership

`e2e_auto_loop.py` owns `adwi/notes/e2e-auto-loop/running.pid` **exclusively**:
- Written immediately on acquiring the lock (after stale check)
- Removed in the `finally` block on any exit (success, failure, cancel, exception)

`server.py` **reads** `running.pid` to check for conflicts before launching, but **never writes** it. This avoids a race condition where the launched script would see its own lock as foreign.

Stale lock detection: `os.kill(pid, 0)` — if `ProcessLookupError`, the lock is stale and is overwritten.

---

## 98% Metric Formula

**Authoritative formula** (matches `generate_master_report.py`):

```
1. Load P1 results from <latest large-* session>/results.jsonl
2. Load P2 results from <latest large-p2-* session>/results.jsonl
3. Merge P1 + P2 into combined list
4. Deduplicate: for each result in P1+P2 order, keep first occurrence of each prompt.lower().strip()
5. combined_pct = count(verdict=="pass" in combined) / len(combined) * 100
```

P1 and P2 rates are also computed independently:
```
p1_pct = count(pass in P1) / len(P1) * 100
p2_pct = count(pass in P2) / len(P2) * 100
```

All three are recorded in every cycle report: `p1_pct`, `p2_pct`, `combined_pct`.

---

## Dirty Worktree Protection

Before every patch attempt, the loop runs `git status --short` and checks if any patchable file has uncommitted changes **not made by this job**.

"Made by this job" = a `.bak` snapshot exists in `<job_dir>/snapshots/<filename>.bak` — meaning we already patched it earlier in this cycle.

If a patchable file has **user uncommitted changes** (not our snapshots):
- Loop sets `needs_llm_review: true`
- Writes `stop_reason` explaining which files are dirty
- Stops cleanly with status `needs_llm_review`
- **Does not revert or overwrite** user changes

---

## Eval Session Directory Selection

`_run_eval_and_get_dir()` uses a snapshot-diff approach to locate each eval's output directory deterministically:

1. Before running the eval: snapshot all existing `large-*` (or `large-p2-*`) dirs
2. Run the eval subprocess (P1 timeout 2400s, P2 timeout 1200s)
3. After it exits: diff the set — exactly one new dir must exist
4. If zero or ≥2 new dirs: fail with a clear error listing the ambiguous dirs

This replaces the previous `_find_latest_session()` which was race-prone (another concurrent eval could create a second dir between run and lookup). The eval scripts create `SESSION_DIR` at import time, so each run produces exactly one new dir.

---

## Known Regex Fixes Policy

`KNOWN_REGEX_FIXES` in `e2e_auto_loop.py` is the only autonomous patching mechanism. Rules:

- Start empty — populate only after reviewing an `--analyze-only` cycle report
- Each entry targets a **specific, repeated** failure cluster (≥3 examples, concentrated misroute)
- Each entry must pass `minimum_examples` before it's attempted
- Every fix is snapshotted before application; if `test_nlu_regex.py` passing count drops, it rolls back automatically (regression guard records before/after counts)
- Only `adwi_cli.py`, `run_large_eval.py`, `run_large_eval_p2.py`, and `capabilities.json` are patchable — never `path_validator.py`, `reason_engine.py`, or security-boundary files

**Adding a safe entry** — minimum required fields:
```python
{
    "id":               "FIX-E2E-001",
    "description":      "One-line description of what this fixes",
    "target_intents":   ["intent_name"],
    "target_file":      "adwi/adwi_cli.py",
    "check_pattern":    r"pattern_that_must_exist",   # idempotency guard
    "old_str":          "exact string to replace",
    "new_str":          "replacement string",
    "minimum_examples": 3,   # don't attempt if fewer than N are failing
}
```

---

## Auto-Fix Safety Model (Hybrid Option C)

### Phase A — Deterministic regex fixes (autonomous)
The loop checks `KNOWN_REGEX_FIXES` (in `adwi/e2e_auto_loop.py`) — a list of pre-approved, deterministic string replacements targeting specific NLU routing patterns.

Fix lifecycle per entry:
1. Check: does any currently-failing intent match `target_intents`? Skip if not.
2. Check: does `old_str` exist in the target file? Skip if not (idempotent).
3. Snapshot the target file to `<job_dir>/snapshots/<filename>.bak`
4. Apply `old_str` → `new_str` replacement (one occurrence)
5. Run `py_compile` + `test_nlu_regex.py`
6. If tests regress → rollback from snapshot, record as skipped

Initially empty. Populate entries after reviewing cycle-1 failure reports.

### Phase B — LLM review report (no autonomous action)
If target not reached after Phase A:
- `needs_llm_review: true` in status.json
- `unfixed_clusters` lists the failing intents with example prompts
- Loop stops — human reviews report, applies LLM-assisted fixes manually
- No aider, no Ollama-generated patches

---

## Stop Conditions

| Condition | Status written |
|-----------|---------------|
| combined_pct ≥ target | `success` |
| `--analyze-only`: below target after eval | `analysis_complete` |
| `--dry-run` flag | `dry_run_complete` |
| max_cycles reached | `max_cycles_reached` |
| Preflight fails (py_compile or unit test) | `failed` |
| P1 or P2 eval subprocess fails | `failed` |
| Ambiguous eval session dir (≠ 1 new dir found) | `failed` |
| Monotonic violation (combined_pct drops vs previous cycle) | `failed` |
| Regression guard rollback failure | `failed` |
| Dirty patchable files with uncommitted user changes | `needs_llm_review` |
| Overall job timeout (14400s) | `timeout` |
| `adwi/notes/e2e-auto-loop/cancel` file exists | `cancelled` |
| KeyboardInterrupt | `cancelled` |
| Unexpected exception | `failed` |

---

## Report Locations

```
adwi/notes/e2e-auto-loop/
├── status.json                        ← live status, updated every cycle
├── running.pid                        ← present only while loop is running
├── cancel                             ← create this file to cancel the loop
└── e2e-20260618-103000/               ← per-job directory
    ├── loop.log                       ← background process stdout/stderr
    ├── git-status-at-start.txt        ← git status snapshot when loop started
    ├── cycle-1-report.json            ← per-cycle metrics + patch record
    ├── cycle-2-report.json
    ├── final-report.json              ← written on any loop exit
    └── snapshots/
        └── adwi_cli.py.bak            ← file snapshot before any patch
```

### `status.json` schema

```json
{
  "job_id": "e2e-20260618-103000",
  "status": "running|success|failed|cancelled|needs_llm_review|max_cycles_reached|timeout|dry_run_complete",
  "updated_at": "2026-06-18T10:30:00",
  "target": 98.0,
  "max_cycles": 3,
  "cycle": 2,
  "report_path": "adwi/notes/e2e-auto-loop/e2e-20260618-103000",
  "final_combined_pct": null,
  "needs_llm_review": false,
  "unfixed_clusters": [],
  "stop_reason": null,
  "cycles": [...]
}
```

### `cycle-N-report.json` schema

```json
{
  "cycle": 1,
  "preflight": "pass",
  "analyze_only": false,
  "p1_total": 1834,  "p1_passed": 1754,  "p1_pct": 95.7,
  "p2_total": 570,   "p2_passed": 553,   "p2_pct": 97.0,
  "combined_total": 2283, "combined_passed": 2187, "combined_pct": 95.8,
  "fail_by_intent": {"chat": 18, "status": 3, ...},
  "top_misroutes": {"chat → memory_recall": 5, ...},
  "failure_clusters": [
    {
      "expected_intent": "chat",
      "fail_count": 18,
      "top_misroute": "chat → memory_recall",
      "top_misroute_count": 12,
      "all_misroutes": {"memory_recall": 12, "rag_search": 4, "status": 2},
      "examples": ["just talk to me", "tell me something interesting", ...],
      "router_type": "LLM",
      "suggested_fix_type": "regex_candidate",
      "patchable_files": ["adwi/adwi_cli.py"],
      "patch_note": "No KNOWN_REGEX_FIXES entry targets this intent."
    }
  ],
  "patches_applied": [],
  "patches_skipped": [],
  "needs_llm_review": true,
  "unfixed_clusters": ["chat", "status", "git_status"],
  "duration_s": 2100.0
}
```

`suggested_fix_type` heuristics:
- `regex_candidate`: ≥3 failures, top misroute ≥60% of cluster — a single regex could likely fix it
- `intent_system_candidate`: scattered misroutes — add a clarifying rule to `_INTENT_SYSTEM`
- `manual_review`: ≤2 examples — too few to be confident in a fix

---

## Home Assistant Button Setup

### Current state: YAML-only (not live until HA reloads config)

The buttons are in `adwi/infra/docker/homeassistant-data/ui-lovelace.yaml` and the rest commands are in `configuration.yaml`. To make them live in Home Assistant:

1. SSH or shell into the HA container / host
2. Copy the updated YAML files to HA's config directory (they are already there if you use the infra volume mount)
3. In HA: **Developer Tools → YAML → Reload all YAML** (or restart HA)
4. The "E2E Auto Loop" and "E2E Loop Status" buttons will appear in the Adwi dashboard grid

**Tap behavior:**
- **Tap**: calls `rest_command.adwi_e2e_auto_loop` → POST to n8n webhook → loop starts
- **Hold**: sends iPhone push "E2E Auto Loop started — check /e2e-auto-loop-status for progress"

No secrets are in the HA YAML. The secret is stored only in n8n's environment variables.

---

## n8n Workflow Import Steps

The workflow template is at: `adwi/automation/workflows/adwi-e2e-auto-loop.json`

**Import steps:**
1. Open n8n at http://100.110.47.128:5678
2. Go to **Settings → n8n API** or **Workflows**
3. Click **Import from file** (or paste JSON)
4. Import `adwi-e2e-auto-loop.json`
5. Verify `ADWI_LOCAL_SECRET` is set: **Settings → Variables → Environment variables**
6. Activate the workflow

**Webhook URLs after import:**
- Start: `POST http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop`
- Status: `POST http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop-status`

**Current state: active and live.** Workflow `6192b91d-7c1b-48c2-a0b9-b325ca774fe9` is in n8n, `active=1`, `activeVersionId` set, both webhook endpoints registered and returning HTTP 200. `ADWI_LOCAL_SECRET` is set in the container via `docker-compose.yml` line 34. n8n data volume: `adwi/infra/docker/n8n-data/` (managed by `adwi/infra/docker/docker-compose.yml`).

---

## How to Run Manually

```bash
# Step 1: Dry-run (preflight only, no eval, no patches — always start here)
python3 adwi/e2e_auto_loop.py --dry-run

# Step 2: Analyze-only (run evals, write enriched failure reports, no patches)
# Status written as "analysis_complete"; read failure_clusters in cycle-1-report.json
python3 adwi/e2e_auto_loop.py --analyze-only --max-cycles 1

# Step 3: After reviewing report, add safe entries to KNOWN_REGEX_FIXES, then:
python3 adwi/e2e_auto_loop.py --max-cycles 1   # one patch cycle

# Full loop foreground (takes ~1 hr per cycle, Ollama must be running)
python3 adwi/adwi_cli.py /e2e-auto-loop

# Full loop background
python3 adwi/adwi_cli.py /e2e-auto-loop --background

# Check status
python3 adwi/adwi_cli.py /e2e-auto-loop-status

# Read the latest report
python3 adwi/adwi_cli.py /e2e-auto-loop-report

# Cancel
python3 adwi/adwi_cli.py /e2e-auto-loop-cancel
# Or: touch adwi/notes/e2e-auto-loop/cancel
```

---

## How to Review Patches Before Committing

The loop never auto-commits. After a successful loop run:

1. Check what changed: `git diff`
2. Review the cycle report: `/e2e-auto-loop-report`
3. Check which patches were applied: look at `cycles[].patches_applied` in the report
4. Review each snapshot: `adwi/notes/e2e-auto-loop/<job-id>/snapshots/`
5. If satisfied: `git add -p` to stage only the changes you want
6. Commit via `/backup-now` or git manually

---

## How to Resume After `needs_llm_review`

When the loop stops with `needs_llm_review: true`:

1. Run `/e2e-auto-loop-report` — note the `unfixed_clusters` list
2. Open `adwi/docs/NLU_REPAIR_BACKLOG.md` — check if any failing intent has a documented fix
3. Apply fixes manually or with aider
4. Add the fix to `KNOWN_REGEX_FIXES` in `adwi/e2e_auto_loop.py` if it's deterministic and safe
5. Re-run: `/e2e-auto-loop` — the loop will start a fresh job

**Suggested prompt for LLM-assisted fix generation:**
```
The following NLU intents are failing in the eval. Each one has example prompts
being misclassified. Review _REGEX_INTENTS in adwi_cli.py and propose a minimal
regex fix for each. Do NOT touch path_validator.py, reason_engine.py, or backup.py.

Failing intents: [copy unfixed_clusters from report]
Top misroutes: [copy top_misroutes from report]
```

---

## Troubleshooting

| Problem | Solution |
|---------|---------|
| `running.pid` exists but loop isn't running | `rm adwi/notes/e2e-auto-loop/running.pid` |
| Loop hangs with no output | Check `adwi/notes/e2e-auto-loop/<job-id>/loop.log` |
| 401 from Safe Command API | Ensure `ADWI_LOCAL_SECRET` matches between `config/.env` and n8n env vars |
| HA button shows no response | Check n8n is running (`docker ps`); check webhook URL in `configuration.yaml` |
| Eval times out | P1 timeout is 2400s, P2 is 1200s; check Ollama is running (`ollama list`) |
| Combined metric differs from MASTER_REPORT | Use latest two session dirs as args to `generate_master_report.py` for reference |
| `needs_llm_review` immediately | Patchable file has uncommitted user changes; stash or commit them first |

---

## Safety Invariants

- `X-Adwi-Secret` auth is unchanged and required on all routes
- No arbitrary shell execution added to Safe Command API
- No secrets stored in HA YAML (only in n8n env vars)
- No auto-commit, auto-push, or remote changes
- No Cloudflare Tunnel
- `PathValidator` and `BLOCKED_PATHS` are never touched
- `KNOWN_REGEX_FIXES` starts empty — human must add entries
- Max cycles default: 3; overall timeout: 4 hours
- Cancel sentinel: any process can create `adwi/notes/e2e-auto-loop/cancel` to stop the loop
