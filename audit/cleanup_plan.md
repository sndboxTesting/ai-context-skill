# Workspace Cleanup Plan

This plan classifies workspace files, archives logs, and cleans up empty directories and temporary files safely without breaking system integrity.

## Classification Matrix

### Core System (KEEP)
- `agent-system/` — Shared memory, tasks, and state.
- `anticipation/` — Prediction and execution engine.
- `autolab/` — Workspace self-improvement system.
- `automation/` — Maintenance, plist and background execution rules.
- `bin/` — Primary CLI entrypoints.
- `comms/` — Messaging and email subsystems.
- `goal-engine/` — Planning and execution graph system.
- `identity/` — User profile, tone, and decision identity maps.
- `mcp/` — Model Context Protocol servers and logic.
- `obsidian-vault/` — Knowledge base and canvas files.
- `orchestrator/` — Task routing and model allocation logic.
- `projects/` — User development projects folder.
- `research-engine/` — Codebase research and decision capturing engine.
- `scripts/` — Auxiliary system intelligence tools.
- `system-context/` — Workspace profile and metadata details.
- `tools/` — Code inventory and recommendation details.

### Configurations (PROTECT)
- `opencode.json` (Root) — Used by `swopencode`.
- `GEMINI.md` (Root) — Used by `swgemini`.
- `AGENTS.md` (Root) — Primary agents config.
- `CLAUDE.md` (Root) — Primary Claude config.
- `.agents/AGENTS.md` — Customizations entrypoint.
- `comms/config/*.json` — Communications permissions and settings.
- `mcp/server/config/*.json` — MCP resource mappings and tool policies.
- `orchestrator/router/*.json` — Routing policy configuration.
- `identity/adaptive/*.json` — Identity learning guards.

### Logs (ARCHIVE)
- `comms/mail/logs/*.log` -> Move to `agent-system/logs/archive/mail/` (compressed).
- `comms/imessage/logs/*.log` -> Move to `agent-system/logs/archive/imessage/` (compressed).
- `mcp/server/logs/*.log` -> Move to `agent-system/logs/archive/mcp/` (compressed).
- `automation/reports/*.log` -> Move to `agent-system/logs/archive/automation/` (compressed).
- `autolab/reports/*.log` -> Move to `agent-system/logs/archive/autolab/` (compressed).

### Temp Files & Backups (CLEANUP)
- Empty directories (remove):
  - `obsidian-vault/mcp-config`
  - `obsidian-vault/inbox`
  - `comms/imessage/state/drafts`
  - `mcp/server/cache`
  - `mcp/server/storage/cache`
  - `automation/doctor`
  - `automation/repair`
  - `autolab/sandboxes`
- Real-time generated log leftovers.

### Duplicates & Unclear Files (PRESERVE/FLAG)
- Autolab snapshots: Preserved as they store historic frontiers and rollback points.
- Binaries/Scripts outside `bin/`: Placed in subsystem-specific script folders (e.g. `comms/mail/scripts/`, `mcp/server/scripts/`, etc.). Keep intact as they are called by internal APIs.

---

## Action Plan

### Step 1: Create Log Archive Structure
Create directory: `agent-system/logs/archive/`.

### Step 2: Safe Log Compression & Archiving
Compress `.log` files to `.tar.gz` or `.gz` and store in `agent-system/logs/archive/`. Then clear or truncate the active log files.

### Step 3: Remove Empty Directories
Remove the 8 empty directories identified during the scan to clean up directory trees.

### Step 4: Normalize Naming
Ensure system files are consistent. No action needed as files are already structured properly.
