# skeleton

Canonical agent rules, safety boundaries, identity spec, and shared operating instructions.

## What It Does

- **Canonical rules** — all agents (Claude Code, Codex, others) read these before meaningful work
- **Safety boundaries** — hard limits that agents must never cross
- **Identity spec** — describes how to speak and behave on Suneel's behalf
- **Workflow rules** — guidelines for code changes, commits, and agent handoffs
- **Startup checklist** — ordered steps required at session start
- **Bounded self-upgrade** — rules for how agents may safely extend the workspace

## Key Files

| File | Purpose |
|------|---------|
| `skeleton/rules/AGENT_SYSTEM.md` | Canonical operating rules — source of truth |
| `skeleton/rules/IDENTITY.md` | Identity spec: voice, tone, communication style |
| `skeleton/rules/WORKFLOW_RULES.md` | Code change workflow, commit style, handoffs |
| `skeleton/rules/SAFETY_BOUNDARIES.md` | Hard limits — what agents must NEVER do |
| `skeleton/rules/STARTUP_CHECKLIST.md` | Ordered startup steps (11 files to read) |
| `skeleton/rules/BOUNDED_SELF_UPGRADE.md` | Rules for SAFE self-modification of workspace |

## Safety Boundaries (summary)

Full details in `SAFETY_BOUNDARIES.md`. Key rules:

- **Never** delete files without backup or explicit approval
- **Never** touch billing, accounts, or payment methods
- **Never** send outbound comms (email, iMessage, Slack) without explicit approval
- **Never** run database migrations without explicit approval
- **Never** hard-reset git branches without backup
- **SAFE** actions: read, analyze, search, generate files, append logs — autopilot
- **CONTROLLED** actions: modify configs, install packages — check first
- **HUMAN_REQUIRED** actions: send messages, delete branches, billing — always ask

## Session Startup Order

Agents must read all startup files before meaningful work — defined in `STARTUP_CHECKLIST.md`:

1. `AGENT_SYSTEM.md` → `IDENTITY.md` → `WORKFLOW_RULES.md` → `SAFETY_BOUNDARIES.md` → `STARTUP_CHECKLIST.md`
2. `brain/memory/MEMORY.md` → `brain/memory/DECISIONS.md`
3. `heart/tasks/ACTIVE_TASKS.md` → `brain/memory/SESSION_HANDOFF.md`
4. `spine/state/CURRENT_STATE.json` → `spine/state/WORKSPACE_HEALTH.json`

Shortcut: `agent-start` handles all of this automatically.

## Hands/Bin Rule

Every CLI command in `hands/bin/` MUST be a symlink — never a plain file or copy. Enforced by the test suite (`tests/organs/hands/test_hands.py` checks `os.path.islink()` for every entry).

## Tests

Skeleton rules are static files — no direct test file. Indirectly validated by all other organ tests that require rules files at expected paths. The `test_hands.py` symlink check enforces the hands/bin rule.

*Updated: 2026-06-28*
