# Workflow Rules

## Purpose

These rules tell agents how to work inside Suneel's shared workspace.

## Before Work

1. Read the startup files listed in `AGENT_SYSTEM.md`.
2. Run or mentally follow `agent-start` when practical.
3. Run `duplication-guard <proposed_path> [-i "intent"]` before creating any script or config to verify it conforms to layout and logic-reuse guidelines.
4. Inspect relevant existing files before editing.
5. Check for existing patterns, scripts, or documentation.
6. Avoid creating duplicate systems.
7. Make backups before replacing meaningful files.


Agents should explicitly state "Loading workspace context" before meaningful work.

## During Work

- Keep changes scoped to the requested goal.
- Prefer simple local files, scripts, and symlinks.
- Keep shared state human-readable.
- Use `projects/` for project work unless another location is clearly required.
- Do not store secrets in shared docs.
- If a command might be destructive, stop and get explicit approval.
- Prefer upgrading the current shared system over inventing a parallel system.

## Verification

After changes, verify the actual files, symlinks, permissions, and expected command behavior.

For shared-agent setup, verify:

- Canonical instructions exist.
- Root and global entrypoints point to the canonical instructions or clearly reference them.
- Scripts exist and are executable.
- `CURRENT_STATE.json` is valid JSON.
- `WORKSPACE_HEALTH.json` and `INDEX.json` are valid JSON.
- Backups are recorded when files were replaced.

## Closeout

At the end of meaningful work:

1. Update `SESSION_HANDOFF.md`.
2. Update `ACTIVE_TASKS.md` and `COMPLETED_TASKS.md`.
3. Append to `SESSION_LOG.md`.
4. Update `CURRENT_STATE.json`.
5. Update `WORKSPACE_HEALTH.json` if health changed.
6. Update `MEMORY.md` or `DECISIONS.md` only for durable, important information.

`agent-autoclose` provides a safety net, but agents should still perform intentional closeout when possible. If they miss it, wrapper exit, shell exit, launchd maintenance, or the next startup should checkpoint the session.

## Handoff Quality

A good handoff is short but complete. It should let the next agent continue without re-discovering basic state.

Include:

- User request.
- Files changed.
- Checks run.
- Open tasks.
- Known risks or limitations.
