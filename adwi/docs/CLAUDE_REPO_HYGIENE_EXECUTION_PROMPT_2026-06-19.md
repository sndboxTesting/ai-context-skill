# Claude Prompt: ADWI Repo Hygiene Execution - 2026-06-19

Use this prompt in Claude Code from:

```bash
cd /Users/MAC/SuneelWorkSpace
```

You are continuing ADWI repair after the trust-baseline and master-report regeneration passes. The current verified NLU baseline is clean: `MASTER_REPORT_v2.md` regenerated from `large-20260619-103709` + `large-p2-20260619-104828`, combined 98.4%, safety breaches 0.

Your job in this cycle is repo hygiene only: stop tracking generated/runtime artifacts that are already documented in `adwi/docs/TRACKED_RUNTIME_ARTIFACT_CLEANUP_PLAN.md`, without deleting local files from disk and without committing.

## Approval Gate

Before doing any `git rm --cached`, look for an explicit approval sentence from Suneel in the current Claude session, such as:

```text
I approve non-destructive repo hygiene cleanup: untrack Group A and recommended Group B runtime artifacts from adwi/docs/TRACKED_RUNTIME_ARTIFACT_CLEANUP_PLAN.md.
```

If that explicit approval is absent:

- Do not run `git rm --cached`.
- Do not stage cleanup changes.
- Summarize what would be untracked and ask Suneel for approval.
- You may still run read-only verification commands.

If approval is present:

- Proceed with non-destructive `git rm --cached` only.
- Do not delete files from disk.
- Do not commit or push.
- Do not untrack files in Group C.

## Hard Rules

- Never read, print, modify, or commit secrets. Do not open `secrets/`, `adwi/config/.env`, `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.kube`, `~/Library/Keychains`, `~/Library/Passwords`, `/etc`, `/private`, `/System`, `/usr/lib`, token files, key files, or credential files.
- Do not run `rm`, `rm -rf`, `git reset --hard`, `git checkout --`, or destructive cleanup commands.
- Do not commit or push.
- Do not alter ADWI runtime behavior in this pass.
- Keep `MASTER_REPORT_v2.md`, eval harness scripts, curated reports, schemas, configs, and source artifacts tracked unless the cleanup plan explicitly says otherwise.

## Current Known Good State

Recent verification from Claude handoff:

```text
MASTER_REPORT_v2.md: regenerated, clean
P1: 98.6% / 1834 scenarios
P2: 98.1% / 570 scenarios
Combined dedup: 98.4% / 2283 scenarios
Safety breaches: 0
Regex fast-path: 66.8%
417 NLU regex tests pass
/eval-routing: 30/30
/test-adwi: 4/4
validate-docs: 20/20, 0 warn
```

## Phase 0 - Read Current Cleanup Plan

Read:

```bash
sed -n '1,260p' adwi/docs/TRACKED_RUNTIME_ARTIFACT_CLEANUP_PLAN.md
```

Then run:

```bash
git status --short
git diff --check
git ls-files | rg '(^adwi/knowledge\.db$|^adwi/memory\.db$|^adwi/knowledge\.db-(wal|shm)$|^adwi/logs/adwi_nlu_fast\.jsonl$|^adwi/logs/simlab_failures\.db$|^adwi/notes/e2e-auto-loop/status\.json$|^adwi/logs/simeval/(large|large-p2|session)-|^adwi/evals/routing-results-|^adwi/logs/overnight/|^adwi/rag-db/|^adwi/services/watchers/.*/uploaded-state\.json$|^ollama/)'
```

Confirm the result still matches the cleanup plan. If there are material differences, update the cleanup plan first and stop before untracking.

## Phase 1 - Ensure Ignore Coverage

Inspect `.gitignore` for runtime artifact coverage. It should cover future instances of:

```gitignore
adwi/knowledge.db
adwi/knowledge.db-*
adwi/memory.db
adwi/logs/adwi_nlu_fast.jsonl
adwi/logs/simlab_failures.db
adwi/evals/routing-results-*.json
adwi/notes/e2e-auto-loop/status.json
adwi/notes/e2e-auto-loop/e2e-*/
adwi/logs/simeval/large-*/
adwi/logs/simeval/large-p2-*/
adwi/logs/simeval/session-*/
adwi/.readme-snapshot.json
adwi/logs/overnight/
adwi/rag-db/
adwi/services/watchers/*/uploaded-state.json
ollama/
logs/adwi_nlu_fast.jsonl
logs/simlab_failures.db
```

If any are missing, add them to `.gitignore`.

Do not add broad patterns that would hide source files, docs, configs, schemas, eval seeds, workflow JSON definitions, or curated reports.

## Phase 2 - Execute Non-Destructive Untracking If Approved

Only if Suneel explicitly approved cleanup in this Claude session, run the approved `git rm --cached` commands from the cleanup plan.

Expected approved scope:

- Group A:
  - SQLite databases and WAL files
  - NLU fast-path log
  - routing result snapshots
  - E2E auto-loop cycle reports and status
  - old raw simeval session directories
- Recommended Group B:
  - `adwi/.readme-snapshot.json`
  - `adwi/logs/overnight/`
  - `adwi/rag-db/notes-index.json`
  - `adwi/services/watchers/open-webui-knowledge/uploaded-state.json`
  - `ollama/.ollama/cache/model-recommendations.json`

Do not untrack Group C.

Use commands from the plan, not ad hoc broad untracking. After each group, check:

```bash
git status --short
```

If a command references a path that is not tracked or does not exist, note it and continue with the remaining approved paths.

## Phase 3 - Verify Local Files Still Exist

After untracking, prove files were not deleted from disk:

```bash
test -f adwi/knowledge.db && echo "knowledge.db exists"
test -f adwi/logs/adwi_nlu_fast.jsonl && echo "adwi_nlu_fast.jsonl exists"
test -f adwi/logs/simlab_failures.db && echo "simlab_failures.db exists"
test -d adwi/logs/simeval && echo "simeval dir exists"
```

For directories untracked with `git rm --cached -r`, spot-check at least one local path still exists if it existed before cleanup.

## Phase 4 - Run Fast Verification

Run:

```bash
git diff --check
adwi/.venv/bin/python3 -m py_compile adwi/adwi_cli.py adwi/reason_engine.py adwi/memory.py adwi/nightly.py adwi/path_validator.py adwi/e2e_auto_loop.py adwi/services/mcp/obsidian-bridge/server.py adwi/services/mcp/obsidian-bridge/mcp_server.py adwi/services/mcp/adwi-sandbox/server.py adwi/services/command-api/server.py
adwi/.venv/bin/python3 -m pytest adwi/tests -q
adwi/.venv/bin/python3 -m pytest adwi/simlab/tests -q
adwi/.venv/bin/python3 adwi/adwi_cli.py /eval-routing
adwi/.venv/bin/python3 adwi/adwi_cli.py /test-adwi
adwi/.venv/bin/python3 adwi/bin/validate-docs
```

Do not rerun full P1/P2 eval in this pass unless Suneel explicitly asks.

## Phase 5 - Update Cleanup Plan

Update `adwi/docs/TRACKED_RUNTIME_ARTIFACT_CLEANUP_PLAN.md` with an execution note:

- date/time
- whether approval was present
- groups untracked or not untracked
- files still awaiting approval, if any
- verification results
- reminder that no files were deleted from disk

If cleanup was not approved, update nothing unless the inventory changed.

## Final Response Requirements

End with a section titled `Codex Handoff Summary`.

In `Codex Handoff Summary`, include:

- whether explicit approval was present
- whether `git rm --cached` was run
- groups/files untracked
- `.gitignore` changes
- proof local files still exist
- exact verification commands and results
- remaining tracked runtime artifacts, if any
- whether any Group C files were intentionally preserved
- recommended next Claude prompt focus, likely CommandRegistry parallel dispatch wiring if repo hygiene is clean

Do not say cleanup is complete unless:

- approved untracking was actually run
- local files still exist
- `git status --short` shows expected staged deletions only for untracked runtime artifacts plus any `.gitignore`/plan edits
- all fast verification commands passed
