"""
nlu_fast_path.py — Qdrant-based fast NLU bypass for Adwi.

Problem
-------
Every NLU call currently invokes llama3.1:8b (≈ 350-600 ms cold, 80-150 ms
warm).  For high-confidence, well-attested intents this latency is wasted:
the 74-fixture `nlu_fixtures` Qdrant collection can resolve them in < 10 ms.

Fast-path rule (both conditions must hold):
  1. Top-1 Qdrant score >= SCORE_THRESHOLD (0.88)
  2. Ambiguity gap: top-1 score - top-2 score >= AMBIGUITY_GAP (0.05)
     — prevents bypass when two intents are semantically close

If either condition fails, the fast path returns None and the caller falls
back to the 8B LLM as usual.

Security / audit
----------------
Every fast-path decision is:
  a. Written to logs/adwi_nlu_fast.jsonl (one JSON line per call)
  b. Counted in the module-level _STATS dict (inspectable at runtime)

The audit log never contains raw user text longer than 200 chars, never
contains tokens or API keys (no environment values are logged), and is
append-only (no delete API).

Public API
----------
    result = fast_classify(text, embed_fn)
    # returns dict matching classify_intent() output schema, or None

    stats = get_fast_path_stats()
    # {calls, hits, misses, bypasses, errors}

    reset_stats()
    # zero counters — for test isolation
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

# ── Tunables ──────────────────────────────────────────────────────────────────

SCORE_THRESHOLD = 0.88   # Minimum cosine similarity to trigger bypass
AMBIGUITY_GAP   = 0.05   # top-1 must beat top-2 by at least this margin
TOP_K           = 2      # Retrieve top-2 to compute ambiguity gap

QDRANT_URL      = "http://localhost:6333"
NLU_COLLECTION  = "nlu_fixtures"

# Audit log
_LOG_DIR  = Path(__file__).parent.parent / "logs"
_AUDIT_LOG = _LOG_DIR / "adwi_nlu_fast.jsonl"

# ── Stats ─────────────────────────────────────────────────────────────────────

_STATS_LOCK = threading.Lock()
_STATS: dict[str, int] = {
    "calls":    0,   # total fast_classify() invocations
    "hits":     0,   # calls that met both threshold conditions
    "misses":   0,   # calls where score was too low or gap too small
    "bypasses": 0,   # LLM calls saved (= hits)
    "errors":   0,   # Qdrant/embed failures
}


def get_fast_path_stats() -> dict[str, int]:
    with _STATS_LOCK:
        return dict(_STATS)


def reset_stats() -> None:
    with _STATS_LOCK:
        for k in _STATS:
            _STATS[k] = 0


def _inc(key: str, n: int = 1) -> None:
    with _STATS_LOCK:
        _STATS[key] += n


# ── Audit log ─────────────────────────────────────────────────────────────────

_AUDIT_LOCK = threading.Lock()


def _audit(record: dict[str, Any]) -> None:
    """Append one JSON record to the fast-path audit log (non-blocking)."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, default=str) + "\n"
        with _AUDIT_LOCK:
            with _AUDIT_LOG.open("a", encoding="utf-8") as f:
                f.write(line)
    except OSError:
        pass  # non-critical; never block NLU on log failure


# ── Qdrant search ─────────────────────────────────────────────────────────────


def _qdrant_search(vector: list[float], k: int = TOP_K) -> list[dict]:
    """
    POST /collections/{name}/points/search and return payload list.
    Uses stdlib urllib — no qdrant-client needed.
    Returns [] on any failure.
    """
    import urllib.error
    import urllib.request

    body = json.dumps({
        "vector":       vector,
        "limit":        k,
        "with_payload": True,
        "score_threshold": SCORE_THRESHOLD - 0.15,  # fetch a wider band, filter in-proc
    }).encode()

    url = f"{QDRANT_URL}/collections/{NLU_COLLECTION}/points/search"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw = json.loads(resp.read())
        return raw.get("result", [])
    except Exception as exc:
        log.debug("Qdrant fast-path search failed: %s", exc)
        return []


# ── Core fast-path logic ──────────────────────────────────────────────────────


def fast_classify(
    text: str,
    embed_fn: Optional[Callable[[str], list[float]]] = None,
) -> Optional[dict]:
    """
    Attempt to classify `text` using Qdrant nearest-neighbour lookup.

    Returns a dict matching classify_intent() output schema:
        {"intent": str, "confidence": float, "arguments": dict,
         "analysis": str, "target": str | None}

    Returns None if:
      - embedding fails
      - Qdrant is unreachable
      - top-1 score < SCORE_THRESHOLD
      - ambiguity gap (top-1 - top-2 score) < AMBIGUITY_GAP

    Thread-safe.
    """
    _inc("calls")
    t0 = time.perf_counter()

    # ── 1. Embed the query ────────────────────────────────────────────────────
    vector: Optional[list[float]] = None
    if embed_fn is not None:
        try:
            vector = embed_fn(text)
        except Exception as exc:
            log.debug("fast_classify embed_fn error: %s", exc)

    if vector is None:
        vector = _default_embed(text)

    if vector is None:
        _inc("errors")
        _audit_decision(text, None, None, "error:embed_failed", t0)
        return None

    # ── 2. Qdrant search ──────────────────────────────────────────────────────
    hits = _qdrant_search(vector, k=TOP_K)

    if not hits:
        _inc("errors")
        _audit_decision(text, None, None, "error:qdrant_empty", t0)
        return None

    top1 = hits[0]
    top1_score: float = top1.get("score", 0.0)
    top2_score: float = hits[1].get("score", 0.0) if len(hits) >= 2 else 0.0

    # ── 3. Apply bypass conditions ────────────────────────────────────────────
    score_ok = top1_score >= SCORE_THRESHOLD
    gap_ok   = (top1_score - top2_score) >= AMBIGUITY_GAP

    if not (score_ok and gap_ok):
        _inc("misses")
        reason = "miss:low_score" if not score_ok else "miss:ambiguous"
        _audit_decision(text, top1_score, top2_score, reason, t0)
        return None

    # ── 4. Build output matching classify_intent() schema ─────────────────────
    payload   = top1.get("payload", {})
    intent    = payload.get("intent", "chat")
    args      = payload.get("arguments") or {}
    reasoning = payload.get("reasoning", "")

    # Reconstruct backward-compat `target`
    target = (
        args.get("path")
        or args.get("url")
        or args.get("query")
        or args.get("description")
        or args.get("target")
    )

    result: dict = {
        "intent":     intent,
        "confidence": round(top1_score, 4),
        "arguments":  dict(args),
        "analysis":   f"[fast-path] {reasoning}" if reasoning else "[fast-path]",
        "target":     target,
    }

    _inc("hits")
    _inc("bypasses")
    _audit_decision(text, top1_score, top2_score, f"hit:{intent}", t0, result)
    return result


# ── Default embed via Ollama ──────────────────────────────────────────────────


def _default_embed(text: str) -> Optional[list[float]]:
    """
    Embed via Ollama /api/embeddings (nomic-embed-text).
    Returns None on failure so the fast path degrades gracefully.
    """
    import urllib.request

    body = json.dumps({"model": "nomic-embed-text", "prompt": text}).encode()
    req  = urllib.request.Request(
        "http://localhost:11434/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return data.get("embedding")
    except Exception as exc:
        log.debug("fast_classify default embed failed: %s", exc)
        return None


# ── Audit helper ──────────────────────────────────────────────────────────────


def _audit_decision(
    text: str,
    top1_score: Optional[float],
    top2_score: Optional[float],
    outcome: str,
    t0: float,
    result: Optional[dict] = None,
) -> None:
    record: dict[str, Any] = {
        "ts":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "text_prefix": text[:200],          # never log full text if >200 chars
        "top1_score":  top1_score,
        "top2_score":  top2_score,
        "gap":         round(top1_score - top2_score, 4) if (top1_score and top2_score) else None,
        "outcome":     outcome,
        "latency_ms":  round((time.perf_counter() - t0) * 1000, 2),
    }
    if result:
        record["intent"]     = result.get("intent")
        record["confidence"] = result.get("confidence")
    _audit(record)
