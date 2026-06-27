# 👁️ Eyes — SuneelWorkSpace Organ

## Purpose
Serves FastAPI/WebSocket Control Center dashboards and implements visual screen monitoring.

## What\s Inside
* `dashboard/`: FastAPI servers, visual dashboard layout static CSS/JS files, and pipeline runner daemons.
* `visual/`: Screenshot managers, visual repair engines, and vision-to-implementation managers.

## Key Files
* [eyes/dashboard/server.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/server.py): Main dashboard endpoint manager.
* [eyes/dashboard/execution/health_repair_pipeline.py](file:///Users/MAC/SuneelWorkSpace/eyes/dashboard/execution/health_repair_pipeline.py): 8-stage repair daemon.
* [eyes/visual/visual_repair_agent.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/visual_repair_agent.py): CSS patches auto-healer.
* [eyes/visual/screenshot_manager.py](file:///Users/MAC/SuneelWorkSpace/eyes/visual/screenshot_manager.py): Visual capture helper.

## Provides (to other organs)
* Dashboard frontend view interface on port 7777.
* Executed repair reports.
* Visual CSS bug repairs.

## Needs (from other organs)
* System state records from `spine`.
* Telemetry database statistics from `blood`.
* Model statuses from `heart`.

## CLI Commands
* `workspace-dashboard`: Starts Control Center server.
* `screenshot-take`: Takes live screenshots.
* `visual-monitor`: Background screenshot daemon.
* `visual-repair`: Visual repair queue manager.

## How To Add Something Here
1. Put HTML widgets inside `eyes/dashboard/widgets/`.
2. Add style selectors inside `eyes/dashboard/static/style.css`.
3. Propagate changes via nerve notifications.
