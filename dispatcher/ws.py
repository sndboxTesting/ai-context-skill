#!/usr/bin/env python3
"""P3.7 — Universal workspace entry point. ws "natural language command"

Usage:
  ws "run health check on the workspace"
  ws "what did Claude do yesterday"
  ws "show me arxiv papers on LLMs"
  ws "compare agents on code review"
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from intent_classifier import classify, resolve, CONFIDENCE_THRESHOLD

BIN_DIR = Path(__file__).parent.parent / "bin"
LOG_PATH = Path(__file__).parent / "dispatcher_log.json"


def _log(query: str, intent: str | None, confidence: float, command: str, args: list) -> None:
    log = []
    if LOG_PATH.exists():
        try:
            log = json.loads(LOG_PATH.read_text())
        except Exception:
            pass
    log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "intent": intent,
        "confidence": round(confidence, 4),
        "command": command,
        "args": args,
    })
    # Keep last 200 entries
    LOG_PATH.write_text(json.dumps(log[-200:], indent=2))


def _run_command(command: str, args: list[str]) -> None:
    bin_path = BIN_DIR / command
    if bin_path.exists():
        cmd = [str(bin_path)] + args
    else:
        cmd = [command] + args
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print(f"Command not found: {command}")
        print(f"Make sure '{command}' is in {BIN_DIR}")


def dispatch(query: str) -> None:
    intent_name, confidence, entry, best_agent = resolve(query)

    if intent_name is None or confidence < CONFIDENCE_THRESHOLD:
        # Low confidence — show top candidates and ask
        results = classify(query)
        print(f"I'm not sure what you mean by: \"{query}\"")
        print(f"Did you mean one of these?\n")
        for i, (name, conf, e) in enumerate(results[:3], 1):
            print(f"  {i}. {e['description']} (confidence: {int(conf*100)}%)")
            print(f"     → {e['command']} {' '.join(e.get('args', []))}")
        print(f"\n  0. None of the above")
        try:
            choice = input("\nPick (1-3) or 0 to cancel: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(results[:3]):
                intent_name, confidence, entry = results[idx]
            else:
                print("Cancelled.")
                return
        except (ValueError, KeyboardInterrupt, EOFError):
            print("Cancelled.")
            return

    command = entry["command"]
    args = entry.get("args", [])

    agent_note = f" (routing to {best_agent})" if best_agent else ""
    print(f"→ {entry['description']}{agent_note}")
    print(f"  {command} {' '.join(args)}\n")

    _log(query, intent_name, confidence, command, args)
    _run_command(command, args)


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        print("Examples:")
        print('  ws "run health check"')
        print('  ws "show telemetry for last 7 days"')
        print('  ws "generate hypotheses"')
        sys.exit(0)

    query = " ".join(sys.argv[1:])
    dispatch(query)


if __name__ == "__main__":
    main()
