#!/usr/bin/env python3
"""Adaptive Identity Loop Controller. Manages feedback queues and updates prompt scores."""

import os
import sys
import json
from pathlib import Path

WORKSPACE = Path(os.environ.get('WORKSPACE', Path(__file__).resolve().parent.parent.parent))
FEEDBACK_LOG = WORKSPACE / 'dna/identity/adaptive/feedback_log.json'
INBOX_DIR = WORKSPACE / 'dna/feedback/inbox'
PROCESSED_DIR = WORKSPACE / 'dna/feedback/processed'


def get_log_summary() -> dict:
    if not FEEDBACK_LOG.exists():
        return {"status": "inactive", "total_records": 0, "last_updated": None}
    try:
        data = json.loads(FEEDBACK_LOG.read_text())
        records = data.get("records", [])
        return {
            "status": "active",
            "total_records": len(records),
            "last_updated": data.get("last_updated"),
            "learning_rate": data.get("learning_rate", 0.05)
        }
    except Exception:
        return {"status": "error", "total_records": 0, "last_updated": None}


def main():
    log_info = get_log_summary()
    
    # Count pending files in inbox
    inbox_files = 0
    if INBOX_DIR.exists():
        inbox_files = len([f for f in os.listdir(INBOX_DIR) if f.endswith('.json')])

    # Count processed files in processed
    processed_files = 0
    if PROCESSED_DIR.exists():
        processed_files = len([f for f in os.listdir(PROCESSED_DIR) if f.endswith('.json')])

    print("\n🧬 Adaptive Identity Loop Controller Status\n")
    print(f"  Loop Status:        {log_info['status'].upper()}")
    print(f"  Pending Inbox:      📬 {inbox_files} file(s)")
    print(f"  Processed History:   📁 {processed_files} file(s)")
    print(f"  Feedback Log Count: 📝 {log_info['total_records']} entry/entries")
    if log_info.get("last_updated"):
        print(f"  Last Update Date:   📅 {log_info['last_updated']}")
    if log_info.get("learning_rate"):
        print(f"  Learning Rate:      ⚡ {log_info['learning_rate']}")
    print()


if __name__ == '__main__':
    main()
