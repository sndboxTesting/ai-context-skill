#!/usr/bin/env python3
"""Enhancement logger — appends to blood/logs/enhancements.jsonl"""
import json, os
from datetime import datetime, timezone

WORKSPACE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
LOG_PATH = os.path.join(WORKSPACE, "blood/logs/enhancements.jsonl")


def log(organ: str, description: str) -> None:
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "ts": datetime.now(timezone.utc).isoformat(),
        "organ": organ,
        "description": description,
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_recent(n: int = 10) -> list[dict]:
    try:
        lines = open(LOG_PATH).readlines()
        return [json.loads(l) for l in lines[-n:] if l.strip()]
    except Exception:
        return []


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 3:
        log(sys.argv[1], " ".join(sys.argv[2:]))
    else:
        for e in get_recent(10):
            print(f"[{e.get('date','')}] {e.get('organ','?'):12} {e.get('description','')}")
