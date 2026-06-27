# 🤲 Hands — SuneelWorkSpace Organ

## Purpose
Stores CLI binaries, launchd schedulers, and workspace CI hooks.

## What\s Inside
* `bin/`: CLI script wrappers.
* `scripts/`: Python/Bash runner modules.
* `automation/`: Cron setup configurations.

## Key Files
* [hands/bin/agent-start](file:///Users/MAC/SuneelWorkSpace/hands/bin/agent-start): Workspace session start hook.
* [hands/automation/maintenance/common.sh](file:///Users/MAC/SuneelWorkSpace/hands/automation/maintenance/common.sh): Central path configuration.
* [hands/automation/ci/workspace_ci.py](file:///Users/MAC/SuneelWorkSpace/hands/automation/ci/workspace_ci.py): Test suite controller.

## Provides (to other organs)
* CLI shortcuts and CI validations.

## Needs (from other organs)
* Fallback model targets from `heart`.
* Diagnostic checks from `spine`.

## CLI Commands
* `agent-start`: marks active session checkpoints.
* `agent-finish`: Marks closeouts and logs.
* `agent-doctor`: Checks health rules.
* `agent-repair`: Auto-heals symlinks.
* `workspace-backup`: Packs tar snapshots of the workspace.
* `workspace-ci`: Runs automated unit testing suites.

## How To Add Something Here
1. Put actual implementations in `hands/scripts/`.
2. Symlink entrypoint into `hands/bin/`.
