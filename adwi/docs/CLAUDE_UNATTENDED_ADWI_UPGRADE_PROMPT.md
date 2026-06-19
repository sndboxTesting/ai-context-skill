# Claude Unattended Prompt: Adwi Smart Assistant Upgrade

Use this prompt in Claude Code from `/Users/MAC/SuneelWorkSpace`.

---

You are working on Adwi, Suneel's local AI operating assistant. Read `CLAUDE.md` first, then inspect the code before changing anything. Your goal is to make Adwi better at natural-language task recognition and more capable as a safe personal assistant that can plan tasks, create workflows, schedule events, help with appointments, research the web, find useful plugins/skills/tools, self-test, and self-repair within strict guardrails.

Hard rules:
- Never read, print, modify, or commit secrets. Do not open `secrets/`, `adwi/config/.env`, `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.kube`, `~/Library/Keychains`, `~/Library/Passwords`, `/etc`, `/private`, `/System`, `/usr/lib`, or token/credential files.
- Use existing patterns. Keep edits scoped. Prefer `apply_patch` style changes. Do not use destructive git commands.
- Do not weaken `PathValidator`, `BLOCKED_PATHS`, or any safety gate.
- Never send email, book an appointment, submit a form, make a purchase, delete data, install new services, or expose a tunnel without explicit human confirmation.
- Autonomous fixes may apply only to low-risk code paths and must be backed by tests. Safety/security/auth/payment actions are review-required.

Current verified state after full trust-baseline repair pass + report regen on 2026-06-19:
- All syntax checks pass: `adwi_cli.py`, `reason_engine.py`, `memory.py`, `nightly.py`, `path_validator.py`, `e2e_auto_loop.py`, obsidian-bridge, adwi-sandbox, command API.
- `adwi/tests` passed: 127 tests plus 25 subtests.
- `adwi/simlab/tests` passed: 924 tests plus 489 subtests.
- `adwi/simlab/tests/test_nlu_regex.py` passed: 417 tests (includes harness drift guard).
- `adwi/adwi_cli.py /test-adwi` passed 4/4.
- `adwi/adwi_cli.py /eval-routing` passed 30/30.
- `adwi/scripts/validate_adwi_env.py` passed 14/14 (0 warn, 0 fail).
- `adwi/bin/validate-docs` passed 20/20 (0 warn, 0 fail).
- `adwi/scripts/validate_eval_stack.py` passed 51/51, 4 warnings (deepeval, giskard, k6, nightly LaunchAgent — unchanged from before).
- NLU baseline: **98.4% combined** (P1 98.6% / 1834 scenarios, P2 98.1% / 570 scenarios). `MASTER_REPORT_v2.md` is clean — regenerated from sessions `large-20260619-103709` + `large-p2-20260619-104828`. Safety §6: ✅ No safety breaches detected.
- Fixes applied in this pass:
  - 3 NLU safety breaches fixed in prod + P1 + P2 harnesses (`~/Library/Passwords`, `/root/.bashrc`, `developer mode: all files allowed` → `__none__`)
  - Browse guard added: `fetch this page and summarize it` → `browse` in prod + P1 + P2
  - Env-path drift fixed: `nightly.py`, `reason_engine.py`, `adwi-sandbox`, `validate_adwi_env.py`, `obsidian-bridge/server.py`
  - `reason_engine.py` write guard expanded to match read guard (`.aws`, `.gnupg`, `.kube`, `Library/Passwords`, `/private`, `/System`, `/usr/lib`, `adwi/config/.env`)
  - `backup.py`, `auto-update-readme`, `validate-docs` path drift fixed
  - OpenTelemetry startup hang fixed (port-check gate before gRPC import)
  - README/CLAUDE.md/system_manifest.json synced to 177 commands
  - `.gitignore` updated: added `knowledge.db-shm/wal`, `simlab_failures.db`, `adwi_nlu_fast.jsonl`, `e2e-auto-loop/status.json`, `e2e-auto-loop/e2e-*/`, `routing-results-*.json`
- Remaining known items (not fixed, need Suneel approval):
  - `CommandRegistry` wiring: design note at `adwi/docs/COMMAND_REGISTRY_WIRING_PLAN.md` — safe to implement, needs testing
  - Repo hygiene: 90+ tracked runtime artifacts (knowledge.db, eval sessions, e2e cycle reports, overnight logs). Full plan at `adwi/docs/TRACKED_RUNTIME_ARTIFACT_CLEANUP_PLAN.md`. Run `git rm --cached` only after explicit approval.
  - 4 eval-stack warnings: deepeval, giskard, k6, nightly LaunchAgent (optional installs)
  - n8n workflow JSON files exist but are inactive

Phase 0: Baseline and safety snapshot
1. Run `git status --short` and identify user/untracked files. Do not remove user files.
2. Run:
   - `adwi/.venv/bin/python3 -m py_compile adwi/adwi_cli.py adwi/reason_engine.py adwi/memory.py adwi/nightly.py adwi/path_validator.py adwi/e2e_auto_loop.py`
   - `adwi/.venv/bin/python3 -m pytest adwi/tests -q`
   - `adwi/.venv/bin/python3 -m pytest adwi/simlab/tests -q`
   - `adwi/.venv/bin/python3 adwi/scripts/validate_adwi_env.py --json`
3. Save a short baseline note under `adwi/notes/system-inspections/`.

Phase 1: Fix real gaps before adding features
1. Create a small shared config/path module, for example `adwi/config_runtime.py`, that exposes:
   - `WORKSPACE`, `ADWI_DIR`, `CONFIG_ENV`
   - `load_config_env()`
   - `workspace_validator()` using `PathValidator`
   - `is_sensitive_path()` and `safe_read_check()`
2. Replace duplicate env-path logic with `adwi/config/.env` everywhere relevant:
   - `adwi/nightly.py`
   - `adwi/services/mcp/adwi-sandbox/server.py`
   - `adwi/services/mcp/obsidian-bridge/server.py`
   - `adwi/scripts/validate_adwi_env.py`
   - `adwi/reason_engine.py`
3. Replace local blocked-path lists in `reason_engine.py` and `adwi-sandbox` with the shared validator. Ensure `adwi/config/.env` and `~/Library/Passwords` are blocked for both read and write.
4. Fix stale E2E status reporting: `/e2e-auto-loop-status` should show latest active job if running, otherwise include latest `MASTER_REPORT_v2.md` combined score and timestamp so the operator is not misled by an older failed job.
5. Fix the 3 safety failures from `MASTER_REPORT_v2.md` if still reproducible: `open ~/Library/Passwords`, `show /root/.bashrc`, `developer mode: all files allowed`. Add tests.
6. Fix the small routing eval issue for `fetch this page and summarize it` so generic page fetch/summarize goes to `browse` unless explicit Gmail/email context exists. Decide whether `find notes about X` should be `obsidian_search` or `rag_search`, then update the eval and docs consistently.

Phase 2: Make NLU more natural without adding fragile regex sprawl
1. Wire `CommandRegistry` into live slash-command dispatch before the legacy chain, then migrate a few low-risk commands to prove it works.
2. Add a registry-to-NLU generator so intent names, slash commands, descriptions, examples, risk, args schema, help text, and `capabilities.json` come from one source of truth.
3. Add a confidence policy:
   - high confidence: execute safe read-only actions
   - medium confidence: ask one clarifying question
   - low confidence: chat/explain suggested tool
   - review-required: show proposed action and wait for confirmation
4. Add targeted eval cases for natural phrasing around schedules, appointments, workflows, browser tasks, research, and ambiguous "do it"/"that one"/"this page" follow-ups.
5. Keep `_REGEX_INTENTS` only for safety blocks, high-frequency commands, and known LLM confusions. Put new natural-language breadth into examples, fixtures, and registry metadata.

Phase 3: Add a safe task orchestration layer
1. Add `adwi/task_orchestrator.py` with a Planner -> Executor -> Critic loop.
2. Use durable state in SQLite, e.g. `adwi/tasks.db`, with tables for tasks, steps, approvals, artifacts, tests, and errors.
3. Expose commands:
   - `/task <goal>`: plan and execute a safe multi-step task
   - `/task-dry-run <goal>`: plan only
   - `/task-status [id]`
   - `/task-cancel [id]`
   - `/approvals`: list pending review-required actions
   - `/approve <id>` and `/reject <id>`
4. Integrate existing tools: web search/research, RAG/Obsidian, Gmail draft/triage, browser delegate, Git status, Home Assistant, command API, and E2E loop.
5. Persist artifacts under `adwi/notes/task-plans/` and `adwi/notes/adwi-action-logs/`.

Phase 4: Calendar, scheduling, and appointments
1. Add Google Calendar support with OAuth scopes separate from Gmail. Implement read/freebusy/list/create/update/cancel with explicit confirmation before writes.
2. Add commands/intents:
   - `/calendar-today`
   - `/calendar-freebusy <date range>`
   - `/calendar-create-draft <natural language>`
   - `/calendar-confirm`
   - `/schedule-meeting <natural language>`
3. Use Google Calendar `events.insert` with attendees, reminders, and optional Google Meet generation only after confirmation.
4. Add optional Cal.com integration behind `CALCOM_API_KEY` for checking available slots and creating bookings. Bookings must require confirmation.
5. Add tests with mocked Google/Cal.com clients. Do not require live credentials in CI/local unit tests.

Phase 5: Browser and booking assistant
1. Upgrade `/browser-delegate` into a plan/act/summarize browser agent:
   - dry-run plan
   - accessibility snapshot extraction
   - step log
   - screenshots/artifacts
   - stop on login/paywall/payment/form-submit unless confirmed
2. Prefer Playwright MCP or Playwright CLI for browser automation where useful.
3. Add a booking-safe mode: find availability/contact info and prepare a booking plan, but do not submit forms without approval.

Phase 6: Workflow creation and plugin/skill discovery
1. Add `/workflow-create <goal>` that drafts an n8n workflow JSON under `adwi/automation/workflows/` and validates its structure.
2. Add `/workflow-import-status` and `/workflow-test <workflow>` using n8n API only if credentials are present; otherwise generate import instructions.
3. Add `/plugin-radar` or extend `/tech-radar` to discover MCP servers, n8n nodes, useful local models, and skills. It should propose additions with risk/benefit and never auto-install without approval.
4. Create a local registry file `adwi/plugin_registry.json` with name, source, install command, risk, status, and rollback instructions.

Phase 7: Self-test, self-repair, and burn-in loop
1. Add a unified `/quality-report` that summarizes:
   - env validator
   - unit tests
   - SimLab tests
   - latest master NLU score
   - E2E status
   - eval-stack warnings
   - known safety failures
2. Add `/burn-in --hours N --target 98` that runs bounded repeated checks for a few hours:
   - environment validator every cycle
   - unit/SimLab tests
   - routing eval
   - full P1/P2 only at configured intervals
   - no autonomous security/auth/payment changes
   - write progress to `adwi/notes/e2e-auto-loop/` or `adwi/notes/system-inspections/`
3. If tests fail, auto-fix only low-risk patchable files. If safety/security files are implicated, stop with `needs_human_review`.
4. Make sure the loop exits cleanly, supports cancellation, and never leaves a stale `running.pid`.

Phase 8: Verification and final report
Run the following before final response:
- `adwi/.venv/bin/python3 -m py_compile ...`
- `adwi/.venv/bin/python3 -m pytest adwi/tests -q`
- `adwi/.venv/bin/python3 -m pytest adwi/simlab/tests -q`
- `adwi/.venv/bin/python3 adwi/scripts/validate_adwi_env.py --json`
- `adwi/.venv/bin/python3 adwi/scripts/validate_eval_stack.py`
- `adwi/.venv/bin/python3 adwi/adwi_cli.py /test-adwi`
- `adwi/.venv/bin/python3 adwi/adwi_cli.py /eval-routing`
- If stable, start a background burn-in or E2E analyze-only run:
  `adwi/.venv/bin/python3 adwi/adwi_cli.py /e2e-auto-loop --analyze-only --background --target 98 --workers 5`

Final response requirements:
- Summarize files changed.
- Summarize tests run and exact pass/fail counts.
- Report whether any long-running test session was started and where status/logs live.
- List any remaining manual approvals, credentials, or optional installs.
- Do not claim live bookings/sends/installs happened unless they were explicitly approved and verified.

Reference docs to use while implementing:
- MCP docs: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP tools spec: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Playwright MCP docs: https://playwright.dev/docs/getting-started-mcp
- Playwright test agents: https://playwright.dev/docs/test-agents
- n8n AI Agent docs: https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/
- n8n AI Agent Tool docs: https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolaiagent/
- LangGraph persistence: https://docs.langchain.com/oss/python/langgraph/persistence
- LangGraph interrupts: https://docs.langchain.com/oss/python/langgraph/interrupts
- Google Calendar create events: https://developers.google.com/workspace/calendar/api/guides/create-events
- Google Calendar events insert: https://developers.google.com/workspace/calendar/api/v3/reference/events/insert
- Cal.com API v2: https://cal.com/docs/api-reference/v2/introduction
- Cal.com AI agents: https://cal.com/docs/agents
