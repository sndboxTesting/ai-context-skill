#!/usr/bin/env python3
"""Query telemetry.db — summary, per-agent, per-task-type, anomalies."""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent / "telemetry.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _days_clause(days: int) -> str:
    return f"datetime('now', '-{days} days')"


def summary(days: int = 7) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        f"""
        SELECT agent, task_type,
               COUNT(*) as total,
               ROUND(100.0 * SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_pct,
               ROUND(AVG(duration_ms)) as avg_duration_ms,
               ROUND(AVG(tokens_in)) as avg_tokens_in,
               ROUND(AVG(tokens_out)) as avg_tokens_out
        FROM traces
        WHERE timestamp >= {_days_clause(days)}
        GROUP BY agent, task_type
        ORDER BY agent, task_type
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def by_agent(agent: str, days: int = 7) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        f"""
        SELECT task_type, COUNT(*) as total,
               ROUND(100.0 * SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_pct,
               ROUND(AVG(duration_ms)) as avg_duration_ms
        FROM traces
        WHERE agent=? AND timestamp >= {_days_clause(days)}
        GROUP BY task_type ORDER BY total DESC
        """,
        (agent,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def by_task_type(task_type: str, days: int = 7) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        f"""
        SELECT agent, COUNT(*) as total,
               ROUND(100.0 * SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_pct,
               ROUND(AVG(duration_ms)) as avg_duration_ms
        FROM traces
        WHERE task_type=? AND timestamp >= {_days_clause(days)}
        GROUP BY agent ORDER BY success_pct DESC
        """,
        (task_type,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def anomalies() -> list[dict]:
    """Return (agent, task_type) pairs where 24h avg duration deviates >20% from 7-day baseline."""
    from telemetry_anomaly import detect_anomalies
    return detect_anomalies()


def _print_table(rows: list[dict]) -> None:
    if not rows:
        print("No data.")
        return
    keys = list(rows[0].keys())
    widths = [max(len(str(k)), max((len(str(r[k])) for r in rows), default=0)) for k in keys]
    header = "  ".join(str(k).ljust(w) for k, w in zip(keys, widths))
    sep = "  ".join("-" * w for w in widths)
    print(header)
    print(sep)
    for r in rows:
        print("  ".join(str(r[k]).ljust(w) for k, w in zip(keys, widths)))


def main() -> None:
    """CLI: telemetry-query <summary|agent|task-type|anomalies> [--days N] [--agent X] [--task-type Y]"""
    import argparse
    parser = argparse.ArgumentParser(description="Query telemetry database")
    parser.add_argument("mode", choices=["summary", "agent", "task-type", "anomalies"])
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--agent", default=None)
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.mode == "summary":
        rows = summary(args.days)
    elif args.mode == "agent":
        if not args.agent:
            print("--agent required for 'agent' mode"); sys.exit(1)
        rows = by_agent(args.agent, args.days)
    elif args.mode == "task-type":
        if not args.task_type:
            print("--task-type required for 'task-type' mode"); sys.exit(1)
        rows = by_task_type(args.task_type, args.days)
    elif args.mode == "anomalies":
        rows = anomalies()

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        _print_table(rows)


if __name__ == "__main__":
    main()
