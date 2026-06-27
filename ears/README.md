# 👂 Ears — SuneelWorkSpace Organ

## Purpose
Scans external world feeds and compiles the morning intelligence briefs.

## What\s Inside
* `monitor/`: Feeds scanners (GitHub, Arxiv, RSS).
* `monitor/digest/`: News format builders.

## Key Files
* [ears/monitor/monitor_runner.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/monitor_runner.py): Feeds crawler entrypoint.
* [ears/monitor/digest/digest_builder.py](file:///Users/MAC/SuneelWorkSpace/ears/monitor/digest/digest_builder.py): Morning brief compiling engine.

## Provides (to other organs)
* Formatted daily briefings of external changes.

## Needs (from other organs)
* Active goals data from `heart`.
* Semantic queries from `brain`.

## CLI Commands
* `monitor-run`: Triggers external feeds fetch.
* `morning-brief`: Generates daily briefing report.

## How To Add Something Here
1. Write custom monitors under `ears/monitor/sources/`.
2. Configure targets inside `ears/monitor/config/monitor_config.json`.
