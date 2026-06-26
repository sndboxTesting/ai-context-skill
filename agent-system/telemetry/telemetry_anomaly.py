#!/usr/bin/env python3
"""Detect regressions >20% vs 7-day baseline and write anomalies.json."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "telemetry.db"
ANOMALIES_PATH = Path(__file__).parent / "anomalies.json"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
THRESHOLD = 0.20  # 20% deviation triggers anomaly


def _get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def detect_anomalies() -> list[dict]:
    conn = _get_conn()

    baseline = conn.execute(
        """
        SELECT agent, task_type,
               AVG(duration_ms) as avg_duration,
               AVG(CASE WHEN outcome='success' THEN 1.0 ELSE 0.0 END) as success_rate
        FROM traces
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY agent, task_type
        HAVING COUNT(*) >= 3
        """
    ).fetchall()

    recent = conn.execute(
        """
        SELECT agent, task_type,
               AVG(duration_ms) as avg_duration,
               AVG(CASE WHEN outcome='success' THEN 1.0 ELSE 0.0 END) as success_rate
        FROM traces
        WHERE timestamp >= datetime('now', '-1 days')
        GROUP BY agent, task_type
        HAVING COUNT(*) >= 1
        """
    ).fetchall()
    conn.close()

    baseline_map = {(r["agent"], r["task_type"]): dict(r) for r in baseline}
    anomalies = []

    for r in recent:
        key = (r["agent"], r["task_type"])
        if key not in baseline_map:
            continue
        b = baseline_map[key]

        # Check duration regression
        if b["avg_duration"] and b["avg_duration"] > 0:
            delta = (r["avg_duration"] - b["avg_duration"]) / b["avg_duration"]
            if delta > THRESHOLD:
                anomalies.append({
                    "agent": r["agent"],
                    "task_type": r["task_type"],
                    "metric": "duration_ms",
                    "baseline": round(b["avg_duration"]),
                    "current": round(r["avg_duration"]),
                    "delta_pct": round(delta * 100, 1),
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                })

        # Check success rate regression
        if b["success_rate"] is not None and b["success_rate"] > 0:
            rate_delta = (b["success_rate"] - r["success_rate"]) / b["success_rate"]
            if rate_delta > THRESHOLD:
                anomalies.append({
                    "agent": r["agent"],
                    "task_type": r["task_type"],
                    "metric": "success_rate",
                    "baseline": round(b["success_rate"], 3),
                    "current": round(r["success_rate"], 3),
                    "delta_pct": round(rate_delta * 100, 1),
                    "detected_at": datetime.now(timezone.utc).isoformat(),
                })

    ANOMALIES_PATH.write_text(json.dumps(anomalies, indent=2))
    return anomalies


def main() -> None:
    anomalies = detect_anomalies()
    if not anomalies:
        print("No anomalies detected.")
        return
    print(f"ANOMALIES DETECTED ({len(anomalies)}):")
    for a in anomalies:
        print(f"  [{a['agent']}] {a['task_type']} — {a['metric']} degraded {a['delta_pct']}% "
              f"(baseline: {a['baseline']}, current: {a['current']})")


if __name__ == "__main__":
    main()
