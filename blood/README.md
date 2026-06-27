# 🩸 Blood — SuneelWorkSpace Organ

## Purpose
Records telemetry traces, performance metrics, and logs anomalies.

## What\s Inside
* `telemetry/`: SQLite databases and writers.
* `logs/`: Diagnostic reports and execution journals.

## Key Files
* [blood/telemetry/telemetry_writer.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_writer.py): SQLite telemetry logging script.
* [blood/telemetry/telemetry_anomaly.py](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/telemetry_anomaly.py): Latency peak regressing checker.
* [blood/telemetry/schema.sql](file:///Users/MAC/SuneelWorkSpace/blood/telemetry/schema.sql): Telemetry DB schema.

## Provides (to other organs)
* Persistent execution analytics and anomaly flags.

## Needs (from other organs)
* Subsystem changes events from `hands`.

## CLI Commands
* `telemetry-query`: sqlite query tables.
* `telemetry-anomalies`: Flags latency regression peaks.

## How To Add Something Here
1. Write analytical metrics functions under `blood/telemetry/`.
2. Update sql schemas in `schema.sql` if tables expand.
