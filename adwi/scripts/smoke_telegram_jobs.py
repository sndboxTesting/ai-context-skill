#!/usr/bin/env python3
"""
smoke_telegram_jobs.py — Smoke test for the Telegram job runner.

Submits a real subprocess job through JobRunner (same path used by Telegram
test commands), polls until completion, prints PASS/FAIL per check.
Exits 0 on full pass, 1 on any failure.

Usage:
  python3 adwi/scripts/smoke_telegram_jobs.py
"""
from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
JR_PATH   = WORKSPACE / "adwi" / "services" / "telegram-bridge" / "job_runner.py"


def _load_job_runner():
    spec = importlib.util.spec_from_file_location("job_runner", JR_PATH)
    mod  = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
    spec.loader.exec_module(mod)                    # type: ignore[union-attr]
    return mod


def _wait_done(runner, job_id: str, timeout: float = 20.0) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = runner.status(job_id)
        if j and j["status"] not in ("queued", "running"):
            return j
        time.sleep(0.2)
    return runner.status(job_id)


def _check(label: str, cond: bool, detail: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status}  {label}{suffix}")
    return cond


def main() -> int:
    print("smoke_telegram_jobs.py — Telegram job runner smoke test")
    print(f"  job_runner path: {JR_PATH}")

    if not JR_PATH.exists():
        print(f"  FAIL  job_runner.py not found at {JR_PATH}")
        return 1

    jr_mod = _load_job_runner()

    # Redirect jobs to a tmp dir so we don't pollute real state
    import tempfile
    tmpdir = tempfile.TemporaryDirectory()
    jr_mod.JOBS_DIR  = Path(tmpdir.name)
    jr_mod.JOBS_FILE = Path(tmpdir.name) / "jobs.json"

    runner = jr_mod.JobRunner()
    passed = 0
    total  = 0

    # --- Test 1: successful job ---
    total += 1
    job_id = runner.submit("smoke-pass", [sys.executable, "-c", "print('smoke ok')"])
    ok = _check("submit returns a job ID", bool(job_id) and job_id.startswith("smoke-pass-"))
    passed += ok

    total += 1
    j = _wait_done(runner, job_id, timeout=15)
    ok = _check("job completes with status=succeeded",
                j is not None and j["status"] == "succeeded",
                detail=f"status={j['status'] if j else 'timeout'}")
    passed += ok

    total += 1
    tail = runner.tail_log(job_id)
    ok = _check("job log contains expected output", "smoke ok" in tail,
                detail=repr(tail[:80]))
    passed += ok

    # --- Test 2: failing job ---
    total += 1
    job_id2 = runner.submit("smoke-fail", [sys.executable, "-c", "import sys; sys.exit(42)"])
    j2 = _wait_done(runner, job_id2, timeout=15)
    ok = _check("failing job status=failed",
                j2 is not None and j2["status"] == "failed",
                detail=f"status={j2['status'] if j2 else 'timeout'}")
    passed += ok

    total += 1
    ok = _check("failing job returncode != 0",
                j2 is not None and j2.get("returncode", 0) != 0,
                detail=f"rc={j2.get('returncode') if j2 else '?'}")
    passed += ok

    # --- Test 3: list_recent ---
    total += 1
    recent = runner.list_recent(10)
    ok = _check("list_recent returns both jobs", len(recent) >= 2)
    passed += ok

    # --- Test 4: state file ---
    total += 1
    ok = _check("jobs.json written to disk", jr_mod.JOBS_FILE.exists())
    passed += ok

    tmpdir.cleanup()

    print(f"\n{passed}/{total} checks passed")
    if passed == total:
        print("PASS")
        return 0
    else:
        print("FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
