#!/usr/bin/env python3
"""Brain Context Injector. Searches brain/ for notes relevant to a task."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Path to brain/ directory relative to this script
VAULT_PATH = Path(__file__).resolve().parent.parent
CACHE_PATH = Path(__file__).resolve().parent.parent.parent / "blood/logs/context_cache.json"
TOP_N = 5
CACHE_TTL_SECONDS = 3600


def _load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text())
        now = datetime.now(timezone.utc).timestamp()
        return {k: v for k, v in data.items() if now - v["ts"] < CACHE_TTL_SECONDS}
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def _score_note(note_path: Path, query_tokens: set[str]) -> float:
    try:
        content = note_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0.0

    preview = content[:500].lower()
    note_tokens = _tokenize(preview)
    filename_tokens = _tokenize(note_path.stem)

    hits_content = len(query_tokens & note_tokens)
    hits_filename = len(query_tokens & filename_tokens)

    try:
        age_days = (datetime.now().timestamp() - note_path.stat().st_mtime) / 86400
        recency = max(0, 1 - age_days / 365)
    except Exception:
        recency = 0

    return hits_filename * 3 + hits_content + recency


def inject(task_description: str) -> str:
    """Return a '## Context from brain:' block with top N relevant notes."""
    if not VAULT_PATH.exists():
        return ""

    cache = _load_cache()
    cache_key = task_description[:120]

    if cache_key in cache:
        return cache[cache_key]["result"]

    query_tokens = _tokenize(task_description)
    if not query_tokens:
        return ""

    scored = []
    # Scan all .md files in the brain directory, skipping vector/graph directories
    for note in VAULT_PATH.rglob("*.md"):
        if "vector" in note.parts or "graph" in note.parts:
            continue
        score = _score_note(note, query_tokens)
        if score > 0:
            scored.append((score, note))

    scored.sort(key=lambda x: -x[0])
    top = scored[:TOP_N]

    if not top:
        return ""

    lines = ["## Context from brain:\n"]
    for score, note in top:
        rel = note.relative_to(VAULT_PATH)
        try:
            snippet = note.read_text(encoding="utf-8", errors="ignore")[:300].strip()
        except Exception:
            snippet = ""
        lines.append(f"### {rel}\n{snippet}\n")

    result = "\n".join(lines)

    cache[cache_key] = {"result": result, "ts": datetime.now(timezone.utc).timestamp()}
    _save_cache(cache)

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: brain-inject \"task description\"")
        sys.exit(1)
    task = " ".join(sys.argv[1:])
    result = inject(task)
    if result:
        print(result)
    else:
        print("(no relevant brain context found)")


if __name__ == "__main__":
    main()
