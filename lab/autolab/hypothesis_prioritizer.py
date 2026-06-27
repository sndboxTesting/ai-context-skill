#!/usr/bin/env python3
"""Hypothesis Prioritizer. Ranks and groups hypotheses in lab/autolab/experiment_queue.md."""

import os
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get('WORKSPACE', Path(__file__).resolve().parent.parent.parent))
QUEUE_PATH = WORKSPACE / 'lab/autolab/experiment_queue.md'


def load_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    
    items = []
    try:
        content = QUEUE_PATH.read_text(encoding="utf-8", errors="ignore")
        for line in content.strip().splitlines():
            if not line.strip() or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                items.append({
                    "category": parts[0].strip(),
                    "hypothesis": parts[1].strip()
                })
    except Exception:
        pass
    return items


def main():
    items = load_queue()
    if not items:
        print("\n📥 Experiment queue is empty.")
        print(f"Generate new hypotheses using: hypothesis-generate\n")
        sys.exit(0)

    print(f"\n📋 Ranked Experiment Queue ({len(items)} items)\n")
    
    # Priority order for categories
    priority = {"repair": 1, "performance": 2, "routing": 3, "research": 4}
    
    # Sort items based on priority category first, then hypothesis length (longer might be more detailed)
    items.sort(key=lambda x: (priority.get(x["category"], 99), -len(x["hypothesis"])))

    for i, item in enumerate(items, 1):
        print(f"  {i}. [{item['category'].upper()}] {item['hypothesis']}")
    print()


if __name__ == '__main__':
    main()
