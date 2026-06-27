# 📋 Spine — SuneelWorkSpace Organ

## Purpose
Tracks workspace state files, indexes, audits, and tool maps.

## What\s Inside
* `state/`: Health registers and index stores.
* `tools/`: MCP tool inventory and recommendations.
* `audit/`: Duplicate files audits and CSO reports.

## Key Files
* [spine/state/CURRENT_STATE.json](file:///Users/MAC/SuneelWorkSpace/spine/state/CURRENT_STATE.json): Persistent workspace variables.
* [spine/state/WORKSPACE_HEALTH.json](file:///Users/MAC/SuneelWorkSpace/spine/state/WORKSPACE_HEALTH.json): System health registers.
* [spine/system-context/system_profile.json](file:///Users/MAC/SuneelWorkSpace/spine/system-context/system_profile.json): Platform parameters.

## Provides (to other organs)
* Workspace state registers and tool indexes.

## Needs (from other organs)
* Nerve notification reports from `nervous`.
* Telemetry flags from `blood`.

## CLI Commands
* `workspace-index`: Re-scans indexing patterns.
* `log-enhancement`: Logs updates to main enhancement indices.

## How To Add Something Here
1. Edit tool mappings inside `spine/tools/tool_inventory.json`.
2. Update audit checklist profiles under `spine/audit/`.
