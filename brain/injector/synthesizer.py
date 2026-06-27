#!/usr/bin/env python3
"""Brain Memory Synthesizer. Reads active memory/decisions and prints a structured synthesis."""

import os
import sys
from pathlib import Path

WORKSPACE = Path(os.environ.get('WORKSPACE', Path(__file__).resolve().parent.parent.parent))
MEMORY_FILE = WORKSPACE / 'brain/memory/MEMORY.md'
DECISIONS_FILE = WORKSPACE / 'brain/memory/DECISIONS.md'
HANDOFF_FILE = WORKSPACE / 'brain/memory/SESSION_HANDOFF.md'


def read_file_safe(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def main():
    memory = read_file_safe(MEMORY_FILE)
    decisions = read_file_safe(DECISIONS_FILE)
    handoff = read_file_safe(HANDOFF_FILE)

    print("\n🔮 Brain Memory State Synthesis\n")

    # Summarize Handoff
    print("📋 Latest Session Handoff Summary:")
    if handoff:
        lines = handoff.strip().split('\n')
        # Print lines containing summary or status
        printed = False
        for line in lines:
            if line.startswith('Summary:') or line.startswith('Date:') or line.startswith('- '):
                print(f"  {line}")
                printed = True
        if not printed:
            print("  Handoff file exists but has no recognized summary fields.")
    else:
        print("  ⚠️ No session handoff file found.")

    # Summarize Memory
    print("\n🧠 Core Memory Facts:")
    if memory:
        lines = [line.strip() for line in memory.strip().split('\n') if line.strip().startswith('-')]
        for line in lines[:5]:
            print(f"  {line}")
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more facts in MEMORY.md.")
    else:
        print("  ⚠️ Core memory file MEMORY.md is missing or empty.")

    # Summarize Decisions
    print("\n🏛️ Key Architectural Decisions:")
    if decisions:
        lines = [line.strip() for line in decisions.strip().split('\n') if line.strip().startswith('-')]
        for line in lines[:5]:
            print(f"  {line}")
        if len(lines) > 5:
            print(f"  ... and {len(lines) - 5} more entries in DECISIONS.md.")
    else:
        print("  ⚠️ Decisions log file DECISIONS.md is missing or empty.")
    print()


if __name__ == '__main__':
    main()
