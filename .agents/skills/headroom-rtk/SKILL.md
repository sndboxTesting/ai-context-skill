---
name: headroom-rtk
description: >
  Active when working in any shell-heavy coding task. Ensures Headroom proxy
  is running and RTK token-optimization is applied to all bash commands.
  Triggers on any session involving file editing, bash commands, or git operations.
---

# Headroom + RTK Active

Both token-saving layers are configured for this workspace:

## Headroom Proxy (Context Compression)
- Running at `http://127.0.0.1:8787`
- All API calls route through it automatically via `ANTHROPIC_BASE_URL`
- Saves ~22-30% of context tokens per session via compression

## RTK (CLI Output Compression)
- Bash commands are auto-rewritten by the pre-tool hook
- `git status` → `rtk git status` (60-80% savings)
- `grep ...` → `rtk grep ...` (75% savings)
- `ls ...` → `rtk ls ...` (60% savings)

## Check savings anytime:
```bash
~/.headroom/bin/rtk gain          # RTK CLI savings
~/.local/bin/headroom agent-savings  # Headroom context savings
savings                           # Both at once (shell alias)
```
