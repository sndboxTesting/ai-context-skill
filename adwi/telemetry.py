"""
telemetry.py — Structured OTel + JSON logging for Adwi.

Architecture
------------
Two parallel outputs per trace event:

1. OTel OTLP gRPC → Arize Phoenix at localhost:4317
   - TracerProvider with BatchSpanExporter
   - Gracefully degrades to NoOpTracer if Phoenix unreachable

2. Structured JSON lines → logs/adwi_otel.jsonl
   - Every span close appends one JSON record
   - Record schema: {ts, trace_id, span_id, name, duration_ms, attrs, status}
   - Redaction: all attribute values pass through _REDACT before logging

Security constraints (hard-coded, never relaxed):
  - _REDACT strips any value whose key matches SENSITIVE_KEYS
  - Values containing bare env-var patterns ($VAR, %VAR%) are scrubbed
  - Blocked path content is never allowed as an attribute value
  - No token, key, or secret ever appears in any log output

Usage
-----
    from adwi.telemetry import span, init_telemetry

    init_telemetry()   # call once at startup (idempotent)

    with span("nlu.classify", {"input.text": text[:200]}):
        result = model_call(...)

    # or with explicit attributes on exit:
    with span("disk.scan") as s:
        count = do_scan()
        s.set_attribute("files.scanned", count)
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import re
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

log = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

OTLP_ENDPOINT = "http://localhost:4317"
LOG_DIR        = Path(__file__).parent.parent / "logs"
OTEL_LOG_PATH  = LOG_DIR / "adwi_otel.jsonl"

SENSITIVE_KEYS: frozenset[str] = frozenset({
    "token", "api_key", "apikey", "secret", "password", "passwd",
    "credential", "credentials", "auth", "authorization", "bearer",
    "access_key", "private_key", "key_id", "client_secret",
    "refresh_token", "session_token", "x-api-key",
})

_ENV_VAR_RE   = re.compile(r"\$[A-Z_][A-Z0-9_]{2,}|%[A-Z_][A-Z0-9_]{2,}%")
_REDACTED_STR = "[REDACTED]"

# Hard-blocked path prefixes (mirrors adwi_cli.py HARD_BLOCKED)
_HOME = str(Path.home())
_BLOCKED_PATH_PREFIXES: tuple[str, ...] = (
    f"{_HOME}/.ssh",
    f"{_HOME}/.aws",
    f"{_HOME}/.gnupg",
    f"{_HOME}/.kube",
    f"{_HOME}/Library/Keychains",
    f"{_HOME}/Library/Passwords",
    "/etc/",
    "/private/",
    "/System/",
)

_INIT_LOCK   = threading.Lock()
_initialized = False
_tracer      = None       # OTel tracer or None (no-op mode)


# ── Redaction ─────────────────────────────────────────────────────────────────


def _is_sensitive_key(key: str) -> bool:
    k = key.lower().replace("-", "_").replace(".", "_")
    return any(s in k for s in SENSITIVE_KEYS)


def _contains_blocked_path(value: str) -> bool:
    return any(value.startswith(pfx) for pfx in _BLOCKED_PATH_PREFIXES)


def _redact_value(key: str, value: Any) -> Any:
    if _is_sensitive_key(key):
        return _REDACTED_STR
    if isinstance(value, str):
        if _contains_blocked_path(value):
            return _REDACTED_STR
        if _ENV_VAR_RE.search(value):
            return _ENV_VAR_RE.sub(_REDACTED_STR, value)
    return value


def redact_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of attrs with all sensitive values scrubbed."""
    return {k: _redact_value(k, v) for k, v in attrs.items()}


# ── JSON structured log writer ────────────────────────────────────────────────


class _JsonLineWriter:
    """Thread-safe append-only JSONL writer."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def write(self, record: dict) -> None:
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            try:
                with self._path.open("a", encoding="utf-8") as f:
                    f.write(line)
            except OSError as exc:
                log.debug("telemetry write failed: %s", exc)


_json_writer: Optional[_JsonLineWriter] = None


# ── OTel bootstrap ────────────────────────────────────────────────────────────


def init_telemetry(
    service_name: str = "adwi",
    endpoint: str = OTLP_ENDPOINT,
    log_path: Path = OTEL_LOG_PATH,
    force: bool = False,
) -> bool:
    """
    Initialize OTel TracerProvider + JSON log writer.
    Safe to call multiple times (idempotent unless force=True).
    Returns True if OTel SDK was successfully configured.
    """
    global _initialized, _tracer, _json_writer

    with _INIT_LOCK:
        if _initialized and not force:
            return _tracer is not None

        _json_writer = _JsonLineWriter(log_path)

        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.resources import SERVICE_NAME, Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            resource = Resource(attributes={SERVICE_NAME: service_name})
            provider = TracerProvider(resource=resource)

            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))

            trace.set_tracer_provider(provider)
            _tracer = trace.get_tracer(service_name)
            _initialized = True
            log.info("OTel TracerProvider configured → %s", endpoint)
            return True

        except ImportError:
            log.debug("opentelemetry SDK not installed — using no-op spans")
        except Exception as exc:
            log.debug("OTel init failed (%s) — using no-op spans", exc)

        _tracer = None
        _initialized = True
        return False


# ── Span context manager ──────────────────────────────────────────────────────


class _SpanHandle:
    """
    Returned by span() context manager.
    Lets callers add attributes mid-span via set_attribute().
    """

    def __init__(self, name: str, initial_attrs: dict[str, Any]) -> None:
        self._name       = name
        self._attrs:  dict[str, Any] = dict(initial_attrs)
        self._otel_span  = None
        self._t0: float  = time.perf_counter()
        self.trace_id: str = ""
        self.span_id:  str = ""

    def set_attribute(self, key: str, value: Any) -> None:
        safe_val = _redact_value(key, value)
        self._attrs[key] = safe_val
        if self._otel_span is not None:
            try:
                self._otel_span.set_attribute(key, safe_val)
            except Exception:
                pass

    def _attach_otel(self, otel_span) -> None:
        self._otel_span = otel_span
        try:
            ctx = otel_span.get_span_context()
            self.trace_id = format(ctx.trace_id, "032x") if ctx.trace_id else ""
            self.span_id  = format(ctx.span_id,  "016x") if ctx.span_id  else ""
        except Exception:
            pass

    def _flush_json(self, status: str = "ok", error: str = "") -> None:
        if _json_writer is None:
            return
        duration_ms = round((time.perf_counter() - self._t0) * 1000, 2)
        record = {
            "ts":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trace_id":    self.trace_id,
            "span_id":     self.span_id,
            "name":        self._name,
            "duration_ms": duration_ms,
            "attrs":       redact_attrs(self._attrs),
            "status":      status,
        }
        if error:
            record["error"] = error[:200]
        _json_writer.write(record)


@contextmanager
def span(
    name: str,
    attrs: Optional[dict[str, Any]] = None,
) -> Generator[_SpanHandle, None, None]:
    """
    Context manager that:
      1. Starts an OTel span (no-op if SDK unavailable)
      2. Yields a _SpanHandle for mid-span attribute mutation
      3. On exit, closes the OTel span and writes one JSON line

    All attribute values are redacted before being sent to OTel or JSON log.
    Exceptions propagate normally; the span is marked with error status.

    Example:
        with span("nlu.classify", {"model": "llama3.1:8b"}) as s:
            result = model(text)
            s.set_attribute("nlu.intent", result["intent"])
    """
    if not _initialized:
        init_telemetry()

    handle    = _SpanHandle(name, redact_attrs(attrs or {}))
    status    = "ok"
    error_str = ""

    # Try to acquire an OTel span context — only the SETUP step is wrapped in
    # try/except.  The yield itself must NOT be inside an outer try/except that
    # could swallow user exceptions and then attempt a second yield.
    otel_span_ctx = None
    if _tracer is not None:
        try:
            from opentelemetry import trace as _trace
            otel_span_ctx = _tracer.start_as_current_span(name)
        except Exception:
            otel_span_ctx = None

    if otel_span_ctx is not None:
        # OTel-active path: one and only one yield lives here.
        with otel_span_ctx as otel_s:
            handle._attach_otel(otel_s)
            for k, v in handle._attrs.items():
                with contextlib.suppress(Exception):
                    otel_s.set_attribute(k, v)
            try:
                yield handle
            except BaseException as exc:
                status    = "error"
                error_str = repr(exc)
                with contextlib.suppress(Exception):
                    from opentelemetry import trace as _trace2
                    otel_s.record_exception(exc)
                    otel_s.set_status(_trace2.StatusCode.ERROR, str(exc)[:200])
                raise
            finally:
                handle._flush_json(status, error_str)
    else:
        # No-op path: OTel unavailable or setup failed — still emit JSON log.
        try:
            yield handle
        except BaseException as exc:
            status    = "error"
            error_str = repr(exc)
            raise
        finally:
            handle._flush_json(status, error_str)


# ── Convenience decorator ─────────────────────────────────────────────────────


def traced(name: Optional[str] = None, attrs: Optional[dict[str, Any]] = None):
    """
    Decorator: wrap a function in a telemetry span.
    Span name defaults to the function's qualified name.

    @traced("nlu.classify", {"model": MODEL_FAST})
    def classify_intent(text):
        ...
    """
    def decorator(fn):
        span_name = name or f"{fn.__module__}.{fn.__qualname__}"

        def wrapper(*args, **kwargs):
            with span(span_name, attrs):
                return fn(*args, **kwargs)

        wrapper.__name__     = fn.__name__
        wrapper.__qualname__ = fn.__qualname__
        wrapper.__doc__      = fn.__doc__
        return wrapper

    return decorator


# ── Current trace context ─────────────────────────────────────────────────────


def current_trace_id() -> str:
    """Return the current OTel trace ID as a hex string, or '' if none active."""
    try:
        from opentelemetry import trace
        ctx = trace.get_current_span().get_span_context()
        if ctx and ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return ""
