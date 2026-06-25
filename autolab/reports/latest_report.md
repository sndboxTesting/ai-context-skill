# Autolab Latest Report

Generated: 2026-06-24T21:09:08-0500
Score: 92.0 / 100
Safety gates: passed

## Breakdown

- canonical_links: 12 / 12 - workspace/global entrypoints point to canonical instructions
- required_files: 12 / 12 - 
- json_validity: 12 / 12 - 
- script_executability: 10 / 10 - 
- doctor_health: 12 / 12 - Workspace health: healthy (3 issues)
- info: codex CLI is not on PATH
- info: claude CLI is not on PATH
- info: Additional AGENTS.md/CLAUDE.md files exist; inspect before consolidating
- gstack_integrity: 0 / 0 - ok
- startup_closeout_readiness: 10 / 10 - agent-start and agent-autoclose available
- launchd_maintenance: 8 / 8 - loaded
- duplicate_instruction_drift: 0 / 8 - .agents/AGENTS.md
- documentation_coverage: 8.0 / 8 - 7/7 docs present
- rollback_readiness: 5 / 5 - snapshots and policies ready
- git_awareness: 3 / 3 - dirty worktree; using snapshots

## Top Opportunities

- Improve `duplicate_instruction_drift` (0 / 8).
