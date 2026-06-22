#!/usr/bin/env python3
"""
smoke_telegram_jobs.py — Validates real Telegram test-job argv via JobRunner.

Loads _TEST_JOBS from the Telegram bridge (bot.py) and submits each entry's
argv through a fresh JobRunner (redirected to a temp dir). Verifies every job
completes with exit code 0.  Prints PASS/FAIL per job with last log lines on
failure.  Exits 0 only if every checked job succeeds.

Usage:
  python3 adwi/scripts/smoke_telegram_jobs.py          # all four test jobs
  python3 adwi/scripts/smoke_telegram_jobs.py --quick  # skip /test_all (~2 min)

Phases:
  Phase 1 — JobRunner plumbing (submit / log capture / state file)
  Phase 2 — Real Telegram _TEST_JOBS argv (prove each Telegram test cmd works)
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent.parent
BOT_PATH  = WORKSPACE / "adwi" / "services" / "telegram-bridge" / "bot.py"
JR_PATH   = WORKSPACE / "adwi" / "services" / "telegram-bridge" / "job_runner.py"

# Per-command timeouts (seconds).  /test_all needs the most headroom.
_TIMEOUTS: dict[str, float] = {
    "/test_quick":    120,
    "/test_nlu":       60,
    "/test_obsidian":  60,
    "/test_all":      300,
}
_DEFAULT_TIMEOUT: float = 90


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod  = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
    spec.loader.exec_module(mod)                    # type: ignore[union-attr]
    return mod


def _wait_done(runner, job_id: str, timeout: float) -> dict | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = runner.status(job_id)
        if j and j["status"] not in ("queued", "running"):
            return j
        time.sleep(0.5)
    return runner.status(job_id)


def _check(label: str, cond: bool, detail: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  {status}  {label}{suffix}")
    return cond


def _print_log_tail(runner, job_id: str, n: int = 12) -> None:
    tail = runner.tail_log(job_id)
    lines = tail.splitlines()[-n:]
    if lines:
        print("      Last log lines:")
        for line in lines:
            print(f"        {line}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    quick = "--quick" in sys.argv

    print("smoke_telegram_jobs.py — Telegram job runner smoke test")
    print(f"  bot.py:     {BOT_PATH}")
    print(f"  job_runner: {JR_PATH}")
    if quick:
        print("  mode:       --quick (skips /test_all)")

    for label, path in [("bot.py", BOT_PATH), ("job_runner.py", JR_PATH)]:
        if not path.exists():
            print(f"\n  FAIL  {label} not found at {path}")
            return 1

    # Load job_runner module (clean instance; we control JOBS_DIR below)
    jr_mod = _load_module("smoke_job_runner", JR_PATH)

    # Load bot.py to read _TEST_JOBS.  bot.py creates its own JobRunner at
    # module level — that instance points at the real jobs dir, which is fine
    # since we never use it here.  We only read _TEST_JOBS from bot_mod.
    try:
        bot_mod = _load_module("smoke_bot", BOT_PATH)
    except Exception as exc:
        print(f"\n  FAIL  Could not load bot.py: {exc}")
        return 1

    test_jobs: dict | None = getattr(bot_mod, "_TEST_JOBS", None)
    if not test_jobs:
        print("\n  FAIL  _TEST_JOBS not found in bot.py")
        return 1

    print(f"\n  Found {len(test_jobs)} test job definitions in _TEST_JOBS")

    # Redirect JobRunner to a temp dir — never pollutes adwi/logs/telegram-jobs/
    tmpdir = tempfile.TemporaryDirectory()
    jr_mod.JOBS_DIR  = Path(tmpdir.name)
    jr_mod.JOBS_FILE = Path(tmpdir.name) / "jobs.json"
    runner = jr_mod.JobRunner()

    passed = 0
    total  = 0

    # ── Phase 1: JobRunner plumbing ───────────────────────────────────────────
    print("\n── Phase 1: JobRunner plumbing ──────────────────────────────────────")

    total += 1
    probe_id = runner.submit("smoke-probe", [sys.executable, "-c", "print('probe ok')"])
    j = _wait_done(runner, probe_id, timeout=15)
    ok = _check(
        "runner submits and executes a job",
        j is not None and j["status"] == "succeeded",
        detail=f"status={j['status'] if j else 'timeout'}",
    )
    passed += ok

    total += 1
    tail = runner.tail_log(probe_id)
    ok = _check("runner captures stdout to log", "probe ok" in tail,
                detail=repr(tail[:60]))
    passed += ok

    total += 1
    ok = _check("runner writes jobs.json", jr_mod.JOBS_FILE.exists())
    passed += ok

    total += 1
    fail_id = runner.submit("smoke-fail", [sys.executable, "-c", "import sys; sys.exit(99)"])
    j_fail = _wait_done(runner, fail_id, timeout=15)
    ok = _check(
        "runner marks failed job correctly",
        j_fail is not None and j_fail["status"] == "failed" and j_fail.get("returncode") == 99,
        detail=f"status={j_fail['status'] if j_fail else 'timeout'} rc={j_fail.get('returncode') if j_fail else '?'}",
    )
    passed += ok

    # ── Phase 2: real Telegram test-job argv ──────────────────────────────────
    print("\n── Phase 2: Real Telegram _TEST_JOBS argv ───────────────────────────")

    for tg_cmd, (job_name, argv) in test_jobs.items():
        if quick and tg_cmd == "/test_all":
            print(f"  SKIP  {tg_cmd:<22} (--quick mode)")
            continue

        timeout = _TIMEOUTS.get(tg_cmd, _DEFAULT_TIMEOUT)
        print(f"\n  Submitting {tg_cmd}  (job={job_name!r}, timeout={timeout}s)")
        print(f"    argv: {argv}")

        total += 1
        job_id = runner.submit(job_name, argv)

        # Poll with a dot printed every 5 s so the terminal doesn't look frozen
        deadline = time.time() + timeout
        last_dot = time.time()
        j = None
        while time.time() < deadline:
            j = runner.status(job_id)
            if j and j["status"] not in ("queued", "running"):
                break
            if time.time() - last_dot >= 5:
                print("    …", flush=True)
                last_dot = time.time()
            time.sleep(0.5)
        if j is None:
            j = runner.status(job_id)

        status = j["status"] if j else "timeout"
        rc     = j.get("returncode") if j else "?"
        ok = _check(
            f"{tg_cmd} completes successfully",
            j is not None and j["status"] == "succeeded",
            detail=f"status={status}  rc={rc}",
        )
        passed += ok

        if not ok:
            _print_log_tail(runner, job_id)

    # ── Done ──────────────────────────────────────────────────────────────────
    try:
        tmpdir.cleanup()
    except Exception:
        pass

    print(f"\n{passed}/{total} checks passed")
    if passed == total:
        print("PASS")
        return 0
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
