"""
tests/test_nlu_fast_path.py — Unit tests for nlu_fast_path.py.

Run:
    python3 adwi/tests/test_nlu_fast_path.py -v

Tests cover:
  - Returns None when embed fails
  - Returns None when Qdrant returns empty
  - Returns None when top-1 score < threshold
  - Returns None when ambiguity gap < AMBIGUITY_GAP
  - Returns correct result dict when both conditions pass
  - Output dict has all required classify_intent() schema fields
  - backward-compat `target` field built from args correctly
  - Stats counters increment correctly (calls, hits, misses, errors)
  - Concurrent calls are thread-safe
  - Audit log written on every call
  - Audit log never contains sensitive data (> 200 chars text truncated)
  - reset_stats() zeroes all counters
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import adwi.nlu_fast_path as fp
from adwi.nlu_fast_path import (
    AMBIGUITY_GAP,
    SCORE_THRESHOLD,
    fast_classify,
    get_fast_path_stats,
    reset_stats,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

_FAKE_VECTOR = [0.1] * 768

def _embed_ok(text: str) -> list[float]:
    return _FAKE_VECTOR

def _embed_fail(text: str) -> list[float]:
    raise RuntimeError("embed failure")

def _make_hit(intent: str, score: float, args: dict = None) -> dict:
    return {
        "score":   score,
        "payload": {
            "intent":    intent,
            "arguments": args or {},
            "reasoning": f"test reasoning for {intent}",
        },
    }


# ── Helper: patch Qdrant search ───────────────────────────────────────────────

def _patch_qdrant(hits: list[dict]):
    return patch("adwi.nlu_fast_path._qdrant_search", return_value=hits)


# ── Embed failure ─────────────────────────────────────────────────────────────


class TestEmbedFailure(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_returns_none_when_embed_fn_raises(self):
        with _patch_qdrant([]):
            result = fast_classify("hello", embed_fn=_embed_fail)
        self.assertIsNone(result)

    def test_error_stat_incremented(self):
        with patch("adwi.nlu_fast_path._default_embed", return_value=None):
            fast_classify("hello")
        self.assertEqual(get_fast_path_stats()["errors"], 1)

    def test_calls_stat_incremented_even_on_error(self):
        with patch("adwi.nlu_fast_path._default_embed", return_value=None):
            fast_classify("hello")
        self.assertEqual(get_fast_path_stats()["calls"], 1)


# ── Qdrant empty ──────────────────────────────────────────────────────────────


class TestQdrantEmpty(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_returns_none_when_qdrant_empty(self):
        with _patch_qdrant([]):
            result = fast_classify("show disk usage", embed_fn=_embed_ok)
        self.assertIsNone(result)

    def test_error_stat_on_empty_qdrant(self):
        with _patch_qdrant([]):
            fast_classify("show disk usage", embed_fn=_embed_ok)
        self.assertEqual(get_fast_path_stats()["errors"], 1)


# ── Score below threshold ─────────────────────────────────────────────────────


class TestLowScore(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_returns_none_when_top1_below_threshold(self):
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD - 0.01),
            _make_hit("chat",       SCORE_THRESHOLD - 0.10),
        ]
        with _patch_qdrant(hits):
            result = fast_classify("disk usage", embed_fn=_embed_ok)
        self.assertIsNone(result)

    def test_miss_stat_incremented(self):
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD - 0.01),
            _make_hit("chat",       0.5),
        ]
        with _patch_qdrant(hits):
            fast_classify("disk usage", embed_fn=_embed_ok)
        self.assertEqual(get_fast_path_stats()["misses"], 1)
        self.assertEqual(get_fast_path_stats()["hits"],   0)


# ── Ambiguity gap too small ───────────────────────────────────────────────────


class TestAmbiguityGap(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_returns_none_when_gap_too_small(self):
        top1_score = SCORE_THRESHOLD + 0.05
        top2_score = top1_score - (AMBIGUITY_GAP - 0.01)  # gap < threshold
        hits = [
            _make_hit("disk_usage", top1_score),
            _make_hit("large_files", top2_score),
        ]
        with _patch_qdrant(hits):
            result = fast_classify("disk usage", embed_fn=_embed_ok)
        self.assertIsNone(result)

    def test_miss_stat_on_ambiguous(self):
        top1_score = SCORE_THRESHOLD + 0.05
        top2_score = top1_score - 0.01
        hits = [
            _make_hit("disk_usage",  top1_score),
            _make_hit("large_files", top2_score),
        ]
        with _patch_qdrant(hits):
            fast_classify("disk usage", embed_fn=_embed_ok)
        self.assertEqual(get_fast_path_stats()["misses"], 1)


# ── Successful bypass ─────────────────────────────────────────────────────────


class TestSuccessfulBypass(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def _good_hits(self, intent: str = "disk_usage", args: dict = None) -> list[dict]:
        return [
            _make_hit(intent, SCORE_THRESHOLD + 0.08, args or {}),
            _make_hit("chat",  SCORE_THRESHOLD - 0.05),
        ]

    def test_returns_dict_on_bypass(self):
        with _patch_qdrant(self._good_hits()):
            result = fast_classify("what's eating my disk?", embed_fn=_embed_ok)
        self.assertIsNotNone(result)

    def test_result_has_intent(self):
        with _patch_qdrant(self._good_hits("web_search")):
            result = fast_classify("search the web", embed_fn=_embed_ok)
        self.assertEqual(result["intent"], "web_search")

    def test_result_has_confidence(self):
        with _patch_qdrant(self._good_hits()):
            result = fast_classify("disk space", embed_fn=_embed_ok)
        self.assertAlmostEqual(result["confidence"], SCORE_THRESHOLD + 0.08, places=2)

    def test_result_has_all_schema_fields(self):
        with _patch_qdrant(self._good_hits()):
            result = fast_classify("disk space", embed_fn=_embed_ok)
        for field in ["intent", "confidence", "arguments", "analysis", "target"]:
            with self.subTest(field=field):
                self.assertIn(field, result)

    def test_result_arguments_dict(self):
        with _patch_qdrant(self._good_hits(args={"size_mb": 500})):
            result = fast_classify("files over 500mb", embed_fn=_embed_ok)
        self.assertEqual(result["arguments"]["size_mb"], 500)

    def test_analysis_prefixed_with_fast_path(self):
        with _patch_qdrant(self._good_hits()):
            result = fast_classify("disk", embed_fn=_embed_ok)
        self.assertIn("fast-path", result["analysis"])

    def test_hit_stat_incremented(self):
        with _patch_qdrant(self._good_hits()):
            fast_classify("disk", embed_fn=_embed_ok)
        self.assertEqual(get_fast_path_stats()["hits"],     1)
        self.assertEqual(get_fast_path_stats()["bypasses"], 1)
        self.assertEqual(get_fast_path_stats()["misses"],   0)

    def test_only_one_hit_needed_for_gap(self):
        # When only one Qdrant result, top2_score defaults to 0 → gap = top1_score
        hits = [_make_hit("disk_usage", SCORE_THRESHOLD + 0.10)]
        with _patch_qdrant(hits):
            result = fast_classify("disk", embed_fn=_embed_ok)
        self.assertIsNotNone(result)


# ── target backward-compat ────────────────────────────────────────────────────


class TestTargetField(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def _hit(self, args: dict) -> list[dict]:
        return [
            _make_hit("test_intent", SCORE_THRESHOLD + 0.1, args),
            _make_hit("chat", 0.4),
        ]

    def test_target_from_path(self):
        with _patch_qdrant(self._hit({"path": "/tmp/file.txt"})):
            r = fast_classify("read file", embed_fn=_embed_ok)
        self.assertEqual(r["target"], "/tmp/file.txt")

    def test_target_from_query(self):
        with _patch_qdrant(self._hit({"query": "ollama docs"})):
            r = fast_classify("search ollama", embed_fn=_embed_ok)
        self.assertEqual(r["target"], "ollama docs")

    def test_target_from_url(self):
        with _patch_qdrant(self._hit({"url": "https://example.com"})):
            r = fast_classify("fetch page", embed_fn=_embed_ok)
        self.assertEqual(r["target"], "https://example.com")

    def test_target_none_when_no_args(self):
        with _patch_qdrant(self._hit({})):
            r = fast_classify("disk", embed_fn=_embed_ok)
        self.assertIsNone(r["target"])

    def test_path_priority_over_query(self):
        with _patch_qdrant(self._hit({"path": "/tmp/x", "query": "other"})):
            r = fast_classify("read file", embed_fn=_embed_ok)
        self.assertEqual(r["target"], "/tmp/x")


# ── Stats ─────────────────────────────────────────────────────────────────────


class TestStats(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_reset_zeroes_all_counters(self):
        with _patch_qdrant([]):
            fast_classify("x", embed_fn=_embed_ok)
        reset_stats()
        s = get_fast_path_stats()
        self.assertTrue(all(v == 0 for v in s.values()))

    def test_multiple_calls_accumulate(self):
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD + 0.1),
            _make_hit("chat", 0.4),
        ]
        with _patch_qdrant(hits):
            for _ in range(5):
                fast_classify("disk", embed_fn=_embed_ok)
        self.assertEqual(get_fast_path_stats()["calls"], 5)
        self.assertEqual(get_fast_path_stats()["hits"],  5)

    def test_stats_keys(self):
        s = get_fast_path_stats()
        self.assertEqual(set(s.keys()), {"calls", "hits", "misses", "bypasses", "errors"})


# ── Thread safety ─────────────────────────────────────────────────────────────


class TestThreadSafety(unittest.TestCase):
    def setUp(self):
        reset_stats()

    def test_concurrent_calls_safe(self):
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD + 0.1),
            _make_hit("chat", 0.4),
        ]
        errors = []

        def _call():
            try:
                with _patch_qdrant(hits):
                    fast_classify("disk", embed_fn=_embed_ok)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_call) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        self.assertEqual(get_fast_path_stats()["calls"], 16)


# ── Audit log ─────────────────────────────────────────────────────────────────


class TestAuditLog(unittest.TestCase):
    def setUp(self):
        reset_stats()
        import tempfile
        self._tmp = tempfile.mkdtemp()
        self._orig_log = fp._AUDIT_LOG
        fp._AUDIT_LOG = Path(self._tmp) / "fast.jsonl"

    def tearDown(self):
        fp._AUDIT_LOG = self._orig_log
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_audit_log_written_on_hit(self):
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD + 0.1),
            _make_hit("chat", 0.4),
        ]
        with _patch_qdrant(hits):
            fast_classify("disk", embed_fn=_embed_ok)
        lines = fp._AUDIT_LOG.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)

    def test_audit_log_written_on_miss(self):
        with _patch_qdrant([]):
            fast_classify("disk", embed_fn=_embed_ok)
        lines = fp._AUDIT_LOG.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)

    def test_audit_record_has_outcome(self):
        with _patch_qdrant([]):
            fast_classify("disk", embed_fn=_embed_ok)
        rec = json.loads(fp._AUDIT_LOG.read_text().strip())
        self.assertIn("outcome", rec)

    def test_audit_text_truncated_at_200_chars(self):
        long_text = "x" * 500
        hits = [
            _make_hit("disk_usage", SCORE_THRESHOLD + 0.1),
            _make_hit("chat", 0.4),
        ]
        with _patch_qdrant(hits):
            fast_classify(long_text, embed_fn=_embed_ok)
        rec = json.loads(fp._AUDIT_LOG.read_text().strip())
        self.assertLessEqual(len(rec["text_prefix"]), 200)

    def test_audit_record_has_latency(self):
        with _patch_qdrant([]):
            fast_classify("disk", embed_fn=_embed_ok)
        rec = json.loads(fp._AUDIT_LOG.read_text().strip())
        self.assertIn("latency_ms", rec)
        self.assertGreaterEqual(rec["latency_ms"], 0)


if __name__ == "__main__":
    unittest.main()
