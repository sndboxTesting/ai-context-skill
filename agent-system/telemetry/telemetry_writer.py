#!/usr/bin/env python3
"""Write agent execution traces to telemetry.db."""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "telemetry.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if not DB_PATH.exists() or os.path.getsize(DB_PATH) == 0:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='traces'"
    ).fetchone()
    if not tables:
        conn.executescript(SCHEMA_PATH.read_text())
        conn.commit()


def write_trace(
    agent: str,
    task_type: str,
    outcome: str,
    duration_ms: int = 0,
    tokens_in: int = 0,
    tokens_out: int = 0,
    payload: dict | None = None,
) -> int:
    """Write one trace record. Returns the new row id."""
    if outcome not in ("success", "fail", "partial"):
        raise ValueError(f"outcome must be success/fail/partial, got: {outcome}")

    conn = _get_conn()
    _ensure_schema(conn)
    cur = conn.execute(
        """INSERT INTO traces
           (timestamp, agent, task_type, duration_ms, tokens_in, tokens_out, outcome, payload_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now(timezone.utc).isoformat(),
            agent,
            task_type,
            duration_ms,
            tokens_in,
            tokens_out,
            outcome,
            json.dumps(payload) if payload else None,
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def main() -> None:
    """CLI: telemetry-write <agent> <task_type> <outcome> [duration_ms] [tokens_in] [tokens_out]"""
    if len(sys.argv) < 4:
        print("Usage: telemetry-write <agent> <task_type> <outcome> [duration_ms] [tokens_in] [tokens_out]")
        sys.exit(1)

    agent = sys.argv[1]
    task_type = sys.argv[2]
    outcome = sys.argv[3]
    duration_ms = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    tokens_in = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    tokens_out = int(sys.argv[6]) if len(sys.argv) > 6 else 0

    row_id = write_trace(agent, task_type, outcome, duration_ms, tokens_in, tokens_out)
    print(f"trace:{row_id}")


if __name__ == "__main__":
    main()
