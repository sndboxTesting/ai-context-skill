@~/.claude/RTK.md

# Shared Agent System — SuneelWorkSpace (AGENTS.md)

## README Blueprint Boot

`~/SuneelWorkSpace/README.md` is the executable system blueprint. Agents must follow its `Session Boot (Mandatory)` section before meaningful work.

## Identity Capture

Before drafting, planning, or communicating for Suneel, load the identity subsystem:

- `~/SuneelWorkSpace/dna/identity/prompts/identity_prompt.md`
- `~/SuneelWorkSpace/dna/identity/prompts/communication_prompt.md`
- `~/SuneelWorkSpace/dna/identity/profile/identity_profile.md`
- `~/SuneelWorkSpace/dna/identity/profile/tone_profile.md`
- `~/SuneelWorkSpace/dna/identity/profile/decision_profile.md`

Apply Suneel's voice: short, direct, casual, conversational, smart, structured, softened, never harsh or condescending. Default to safe autopilot, but ask before serious system risk, destructive actions, money/account actions, or outbound communication.

## Purpose

This is the canonical instruction source for Suneel's living shared agent workspace at `~/SuneelWorkSpace`.
Claude Code, Codex CLI, and other agents all share this workspace for instructions, memory, tasks, logs, and state.

## Source Of Truth

- Canonical workspace: `~/SuneelWorkSpace`
- Canonical instructions: `~/SuneelWorkSpace/skeleton/rules/AGENT_SYSTEM.md`
- Entrypoints: `~/SuneelWorkSpace/CLAUDE.md` and `~/SuneelWorkSpace/AGENTS.md`
- Customization customizations: `~/SuneelWorkSpace/.agents/AGENTS.md`
- Memory files: `~/SuneelWorkSpace/brain/memory/`

## Startup

Before meaningful work, read these files in order:

1. `~/SuneelWorkSpace/skeleton/rules/AGENT_SYSTEM.md`
2. `~/SuneelWorkSpace/skeleton/rules/IDENTITY.md`
3. `~/SuneelWorkSpace/skeleton/rules/WORKFLOW_RULES.md`
4. `~/SuneelWorkSpace/skeleton/rules/SAFETY_BOUNDARIES.md`
5. `~/SuneelWorkSpace/skeleton/rules/STARTUP_CHECKLIST.md`
6. `~/SuneelWorkSpace/brain/memory/MEMORY.md`
7. `~/SuneelWorkSpace/brain/memory/DECISIONS.md`
8. `~/SuneelWorkSpace/heart/tasks/ACTIVE_TASKS.md`
9. `~/SuneelWorkSpace/heart/tasks/TASK_QUEUE.md`
10. `~/SuneelWorkSpace/brain/memory/SESSION_HANDOFF.md`
11. `~/SuneelWorkSpace/spine/state/CURRENT_STATE.json`
12. `~/SuneelWorkSpace/spine/state/WORKSPACE_HEALTH.json`

Use `~/SuneelWorkSpace/hands/bin/agent-start` or `~/SuneelWorkSpace/hands/bin/workspace-context` to print the startup brief.

Mandatory startup behavior:
- State: "Loading workspace context".
- Read startup checklist files.
- Summarize current state, health, tasks, and handoff.
- If a previous session was open, run or rely on `agent-autoclose --startup-recovery` recovery.

## Closeout

After completing meaningful work, update:
- `brain/memory/SESSION_HANDOFF.md`
- `heart/tasks/ACTIVE_TASKS.md` and/or `heart/tasks/COMPLETED_TASKS.md`
- `blood/logs/SESSION_LOG.md`
- `spine/state/CURRENT_STATE.json`
- `spine/state/WORKSPACE_HEALTH.json` if health changed
- `brain/memory/MEMORY.md` or `brain/memory/DECISIONS.md` if durable knowledge was created

Use `~/SuneelWorkSpace/hands/bin/agent-finish "summary"` to mark session end.

## Rules

- Keep shared state file-based, transparent, and easy to inspect.
- Avoid money-related actions and billing changes.
- Avoid destructive actions (never delete/overwrite important files without backup).
- New CLI commands must always be symlinked inside `hands/bin/` — never copied.
- Notify nervous subscribers of changes: `python3 nervous/nerve_propagator.py notify <organ> "update" <path>`.

## Nerve System & Human Body Architecture
The workspace is structured into 12 Organs (folders) interconnected via `nervous/nerve_propagator.py` events:
- **brain**: vector search memory, anticipation, research.
- **heart**: goals scheduler, task queues, model fallback router.
- **eyes**: control center Web dashboard, visual screenshot healer.
- **ears**: external RSS/GitHub monitors, morning briefing builder.
- **nervous**: gateway gateway, central MCP connectors, nerve propagator.
- **skeleton**: shared instructions, safety gates, rules markdown files.
- **blood**: SQLite telemetry databases, logs anomaly indicators.
- **hands**: scripts executables, launchd plist automation, CI runner.
- **mouth**: ws dispatcher, communication plugins (Mail, iMessage).
- **dna**: identity prompt models, adapt loop scorers.
- **lab**: autolab experiments, self-evolution challenger cycles.
- **spine**: health profiles, workspace current index registers.

## Token Optimization & RTK
* **Headroom proxy**: Run proxy on port 8787 via `ANTHROPIC_BASE_URL` to compress context.
* **RTK hook**: Pre-tool execution auto-rewriter reduces CLI output tokens by 50-90%.
* **RTK Commands**: Always prefix bash commands with `rtk` (e.g. `rtk git status`, `rtk cargo test`, `rtk next build`).

<!-- rtk-instructions v2 -->

# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->
