"""
tests/test_telemetry.py — Unit tests for adwi.telemetry.

Run:
    python3 adwi/tests/test_telemetry.py -v

Tests cover:
  - Redaction of sensitive keys (token, api_key, secret, etc.)
  - Redaction of env-var patterns ($VAR, %VAR%)
  - Redaction of blocked path prefixes (~/.ssh, /etc, etc.)
  - Safe passthrough for normal values
  - span() context manager writes JSON log entry
  - span() propagates exceptions (error status in log)
  - set_attribute() on _SpanHandle redacts correctly
  - traced() decorator wraps correctly
  - init_telemetry() is idempotent
  - JSON log record has required schema fields
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import adwi.telemetry as tel
from adwi.telemetry import (
    _SpanHandle,
    _is_sensitive_key,
    _redact_value,
    redact_attrs,
    span,
    traced,
)


# ── Redaction logic ───────────────────────────────────────────────────────────


class TestIsInsideOrEqual(unittest.TestCase):
    """Sensitive key detection."""

    def test_exact_sensitive_keys(self):
        for key in ["token", "api_key", "secret", "password", "bearer"]:
            with self.subTest(key=key):
                self.assertTrue(_is_sensitive_key(key))

    def test_compound_sensitive_keys(self):
        for key in ["auth_token", "client.secret", "x-api-key", "access_key_id"]:
            with self.subTest(key=key):
                self.assertTrue(_is_sensitive_key(key))

    def test_non_sensitive_keys(self):
        for key in ["model", "intent", "duration_ms", "query", "path", "files"]:
            with self.subTest(key=key):
                self.assertFalse(_is_sensitive_key(key))


class TestRedactValue(unittest.TestCase):
    def test_sensitive_key_value_redacted(self):
        self.assertEqual(_redact_value("api_key", "sk-abc123"), "[REDACTED]")

    def test_sensitive_key_redacted_regardless_of_value(self):
        self.assertEqual(_redact_value("token", ""), "[REDACTED]")

    def test_env_var_dollar_redacted(self):
        result = _redact_value("query", "get $OPENAI_API_KEY from env")
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("$OPENAI_API_KEY", result)

    def test_env_var_percent_redacted(self):
        result = _redact_value("query", "value is %SECRET_KEY%")
        self.assertIn("[REDACTED]", result)

    def test_blocked_path_redacted(self):
        home = str(Path.home())
        result = _redact_value("path", f"{home}/.ssh/id_rsa")
        self.assertEqual(result, "[REDACTED]")

    def test_etc_path_redacted(self):
        result = _redact_value("file", "/etc/passwd")
        self.assertEqual(result, "[REDACTED]")

    def test_normal_string_passes_through(self):
        result = _redact_value("model", "llama3.1:8b")
        self.assertEqual(result, "llama3.1:8b")

    def test_integer_passes_through(self):
        result = _redact_value("count", 42)
        self.assertEqual(result, 42)

    def test_float_passes_through(self):
        result = _redact_value("confidence", 0.91)
        self.assertAlmostEqual(result, 0.91)

    def test_none_passes_through(self):
        result = _redact_value("target", None)
        self.assertIsNone(result)


class TestRedactAttrs(unittest.TestCase):
    def test_mixed_dict_redacted(self):
        attrs = {
            "intent":   "web_search",
            "api_key":  "sk-secret",
            "query":    "ollama docs",
            "token":    "abc",
        }
        out = redact_attrs(attrs)
        self.assertEqual(out["intent"], "web_search")
        self.assertEqual(out["api_key"], "[REDACTED]")
        self.assertEqual(out["query"], "ollama docs")
        self.assertEqual(out["token"], "[REDACTED]")

    def test_original_dict_unchanged(self):
        attrs = {"secret": "xyz", "ok": "value"}
        _ = redact_attrs(attrs)
        self.assertEqual(attrs["secret"], "xyz")  # not mutated


# ── JSON log writer ───────────────────────────────────────────────────────────


class TestJsonLineWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_path = Path(self.tmp) / "test_otel.jsonl"

    def _init(self):
        tel.init_telemetry(log_path=self.log_path, force=True)

    def test_span_writes_one_json_line(self):
        self._init()
        with span("test.basic", {"k": "v"}):
            pass
        lines = self.log_path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)

    def test_json_record_has_required_fields(self):
        self._init()
        with span("test.fields", {"model": "llama3"}):
            pass
        rec = json.loads(self.log_path.read_text().strip())
        for field in ["ts", "name", "duration_ms", "attrs", "status"]:
            with self.subTest(field=field):
                self.assertIn(field, rec)

    def test_span_name_in_record(self):
        self._init()
        with span("my.special.span"):
            pass
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["name"], "my.special.span")

    def test_attrs_in_record(self):
        self._init()
        with span("test.attrs", {"intent": "disk_usage", "count": 5}):
            pass
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["attrs"]["intent"], "disk_usage")
        self.assertEqual(rec["attrs"]["count"], 5)

    def test_sensitive_attrs_redacted_in_json(self):
        self._init()
        with span("test.redact", {"token": "bearer abc", "query": "ok"}):
            pass
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["attrs"]["token"], "[REDACTED]")
        self.assertEqual(rec["attrs"]["query"], "ok")

    def test_duration_ms_is_positive(self):
        self._init()
        with span("test.timing"):
            time.sleep(0.01)
        rec = json.loads(self.log_path.read_text().strip())
        self.assertGreater(rec["duration_ms"], 0)

    def test_status_ok_on_success(self):
        self._init()
        with span("test.ok"):
            pass
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["status"], "ok")

    def test_status_error_on_exception(self):
        self._init()
        with self.assertRaises(ValueError):
            with span("test.error"):
                raise ValueError("intentional")
        last_line = self.log_path.read_text().strip().splitlines()[-1]
        rec = json.loads(last_line)
        self.assertEqual(rec["status"], "error")
        self.assertIn("error", rec)
        self.assertIn("ValueError", rec["error"])

    def test_multiple_spans_append_multiple_lines(self):
        self._init()
        for i in range(3):
            with span(f"test.multi.{i}"):
                pass
        lines = self.log_path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 3)

    def test_concurrent_spans_all_logged(self):
        self._init()
        errors = []

        def _do_span(i):
            try:
                with span(f"concurrent.{i}", {"i": i}):
                    time.sleep(0.002)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_do_span, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        lines = self.log_path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 8)


# ── _SpanHandle ───────────────────────────────────────────────────────────────


class TestSpanHandle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_path = Path(self.tmp) / "handle.jsonl"
        tel.init_telemetry(log_path=self.log_path, force=True)

    def test_set_attribute_appears_in_log(self):
        with span("test.handle") as s:
            s.set_attribute("nlu.intent", "disk_usage")
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["attrs"]["nlu.intent"], "disk_usage")

    def test_set_attribute_redacts_sensitive(self):
        with span("test.handle.redact") as s:
            s.set_attribute("api_key", "secret-value")
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["attrs"]["api_key"], "[REDACTED]")

    def test_initial_and_mid_span_attrs_merged(self):
        with span("test.merged", {"initial": "yes"}) as s:
            s.set_attribute("added", "later")
        rec = json.loads(self.log_path.read_text().strip())
        self.assertEqual(rec["attrs"]["initial"], "yes")
        self.assertEqual(rec["attrs"]["added"], "later")


# ── traced() decorator ────────────────────────────────────────────────────────


class TestTracedDecorator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.log_path = Path(self.tmp) / "traced.jsonl"
        tel.init_telemetry(log_path=self.log_path, force=True)

    def test_traced_wraps_function(self):
        @traced("test.traced")
        def my_fn():
            return 42

        result = my_fn()
        self.assertEqual(result, 42)

    def test_traced_logs_span(self):
        @traced("test.traced.log")
        def compute():
            return "done"

        compute()
        lines = self.log_path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        rec = json.loads(lines[0])
        self.assertEqual(rec["name"], "test.traced.log")

    def test_traced_propagates_exceptions(self):
        @traced("test.traced.exc")
        def bad_fn():
            raise RuntimeError("oops")

        with self.assertRaises(RuntimeError):
            bad_fn()
        last_line = self.log_path.read_text().strip().splitlines()[-1]
        rec = json.loads(last_line)
        self.assertEqual(rec["status"], "error")

    def test_traced_preserves_function_name(self):
        @traced()
        def my_named_fn():
            pass

        self.assertEqual(my_named_fn.__name__, "my_named_fn")


# ── init_telemetry() idempotency ──────────────────────────────────────────────


class TestInitIdempotency(unittest.TestCase):
    def test_second_call_does_not_crash(self):
        tmp = tempfile.mkdtemp()
        p = Path(tmp) / "idem.jsonl"
        tel.init_telemetry(log_path=p, force=True)
        tel.init_telemetry(log_path=p)  # second call — should be no-op
        with span("idem.test"):
            pass
        lines = p.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)


if __name__ == "__main__":
    unittest.main()
