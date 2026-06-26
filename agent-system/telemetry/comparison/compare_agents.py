#!/usr/bin/env python3
"""P3.3 — Cross-agent leaderboard. Reads telemetry.db, computes capability scores."""

import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "telemetry.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema.sql"
LEADERBOARD_PATH = Path(__file__).parent / "leaderboard.json"


def _get_conn() -> sqlite3.Connection:
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _capability_score(success_rate: float, avg_duration_ms: float, max_duration_ms: float) -> float:
    """score = 0.87 * success_rate + 0.13 * (1 - normalized_latency)"""
    normalized_latency = (avg_duration_ms / max_duration_ms) if max_duration_ms > 0 else 0
    return round(0.87 * success_rate + 0.13 * (1 - normalized_latency), 4)


def compute_leaderboard(days: int = 7) -> dict:
    conn = _get_conn()
    rows = conn.execute(
        f"""
        SELECT agent, task_type,
               COUNT(*) as total,
               AVG(CASE WHEN outcome='success' THEN 1.0 ELSE 0.0 END) as success_rate,
               AVG(duration_ms) as avg_duration_ms,
               MAX(duration_ms) as max_duration_ms
        FROM traces
        WHERE timestamp >= datetime('now', '-{days} days')
        GROUP BY agent, task_type
        HAVING COUNT(*) >= 1
        """
    ).fetchall()
    conn.close()

    # Find global max duration per task_type for normalization
    max_by_task: dict[str, float] = {}
    for r in rows:
        key = r["task_type"]
        if r["max_duration_ms"]:
            max_by_task[key] = max(max_by_task.get(key, 0), r["max_duration_ms"])

    leaderboard: dict[str, dict] = {}
    for r in rows:
        task_type = r["task_type"]
        agent = r["agent"]
        score = _capability_score(
            r["success_rate"] or 0,
            r["avg_duration_ms"] or 0,
            max_by_task.get(task_type, 1),
        )
        if task_type not in leaderboard:
            leaderboard[task_type] = {}
        leaderboard[task_type][agent] = {
            "capability_score": score,
            "success_rate": round(r["success_rate"] or 0, 4),
            "avg_duration_ms": round(r["avg_duration_ms"] or 0),
            "total_traces": r["total"],
        }

    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEADERBOARD_PATH.write_text(json.dumps(leaderboard, indent=2))
    return leaderboard


def best_agent_for(task_type: str) -> str | None:
    """Return agent with highest capability score for given task_type."""
    if not LEADERBOARD_PATH.exists():
        compute_leaderboard()
    lb = json.loads(LEADERBOARD_PATH.read_text())
    agents = lb.get(task_type, {})
    if not agents:
        return None
    return max(agents, key=lambda a: agents[a]["capability_score"])


def compare(task_type: str | None = None, days: int = 7) -> None:
    lb = compute_leaderboard(days)

    tasks = [task_type] if task_type else sorted(lb.keys())
    for tt in tasks:
        agents = lb.get(tt, {})
        if not agents:
            continue
        print(f"\n── {tt} ──")
        # Header
        print(f"  {'Agent':<12} {'Score':>7} {'Success%':>10} {'Avg ms':>8} {'Traces':>7}")
        print(f"  {'-'*12} {'-'*7} {'-'*10} {'-'*8} {'-'*7}")
        for agent, stats in sorted(agents.items(), key=lambda x: -x[1]["capability_score"]):
            print(f"  {agent:<12} {stats['capability_score']:>7.4f} "
                  f"{stats['success_rate']*100:>9.1f}% "
                  f"{stats['avg_duration_ms']:>8} "
                  f"{stats['total_traces']:>7}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Compare agent performance")
    parser.add_argument("--task-type", default=None)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--best", action="store_true", help="Print best agent for task-type")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.best:
        if not args.task_type:
            print("--task-type required with --best"); sys.exit(1)
        agent = best_agent_for(args.task_type)
        print(agent or "no data")
        return

    if args.json:
        lb = compute_leaderboard(args.days)
        print(json.dumps(lb, indent=2))
    else:
        compare(args.task_type, args.days)


if __name__ == "__main__":
    main()
