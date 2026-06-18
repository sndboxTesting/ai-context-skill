# E2E Auto Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bounded NLU eval→analyze→fix→retest loop triggered from a Home Assistant phone button, stopping at ≥98% combined pass rate or a safety/iteration limit.

**Architecture:** Standalone `e2e_auto_loop.py` owns lock/status files and runs sequentially; `server.py` gains a Popen start route returning in <1s; `adwi_cli.py` gains 4 commands (foreground default, `--background` to detach); HA → n8n → Safe Command API → detached background process → `adwi/notes/e2e-auto-loop/` status files.

**Tech Stack:** Python 3.11 stdlib only (subprocess, argparse, json, pathlib, shutil), Home Assistant YAML (rest_command + button), n8n JSON workflow template.

## Global Constraints

- `e2e_auto_loop.py` MUST NOT import `adwi_cli.py` or any production Adwi module
- PID lock ownership: `e2e_auto_loop.py` writes and removes `running.pid` exclusively; `server.py` only reads it
- Auto-fix: only `KNOWN_REGEX_FIXES` table — no aider, no Ollama LLM generation
- Combined metric formula: dedup-merge P1+P2 `results.jsonl` on `prompt.lower().strip()`, count `verdict=="pass"` / total × 100 (matches `generate_master_report.py`)
- Dirty-worktree guard: check `git status --short` before patching; abort if patchable file has uncommitted user changes not made by this job
- Monotonic guard: if `combined_pct` decreases vs previous cycle, rollback all cycle snapshots and stop with `status: failed`
- Snapshot every patchable file before touching it; rollback from snapshot on any preflight/test regression
- Never touch: `path_validator.py`, `reason_engine.py`, `backup.py`, `secrets/`, Gmail send code, HA secrets YAML
- No auto-commit, no auto-push, no remote changes
- Timeouts: P1 eval 2400s, P2 eval 1200s, overall job 14400s (4 hr)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `adwi/e2e_auto_loop.py` | Create | Core loop engine: lock, eval, metrics, patch, finalize |
| `adwi/bin/adwi-e2e-status-reader` | Create | Read-only status/report/cancel helper (prints JSON) |
| `adwi/services/command-api/server.py` | Modify | Add Popen start handler + 3 read-only routes |
| `adwi/adwi_cli.py` | Modify | Add 4 `cmd_e2e_*` functions + dispatch lines + help text |
| `adwi/infra/docker/homeassistant-data/configuration.yaml` | Modify | Add 2 `rest_command` entries |
| `adwi/infra/docker/homeassistant-data/ui-lovelace.yaml` | Modify | Add 2 buttons to grid |
| `adwi/automation/workflows/adwi-e2e-auto-loop.json` | Create | Importable n8n workflow template |
| `adwi/docs/E2E_AUTO_LOOP.md` | Create | User-facing documentation |

---

### Task 1: `adwi/e2e_auto_loop.py` — Core loop engine

**Files:**
- Create: `adwi/e2e_auto_loop.py`

**Interfaces:**
- Produces: `main(target, max_cycles, dry_run, job_id, workers) -> int` (0=success, 1=failure)
- Produces: `adwi/notes/e2e-auto-loop/running.pid` (written on acquire, removed on release)
- Produces: `adwi/notes/e2e-auto-loop/status.json` (updated every state change)
- Produces: `adwi/notes/e2e-auto-loop/<job_id>/cycle-N-report.json`
- Produces: `adwi/notes/e2e-auto-loop/<job_id>/final-report.json`

- [ ] **Step 1: Create `adwi/e2e_auto_loop.py` with full implementation**

```python
#!/usr/bin/env python3
"""
Adwi E2E Auto Loop — bounded NLU eval → analyze → fix → retest loop.
Standalone: no adwi_cli imports. Owns running.pid exclusively.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from datetime import datetime
from pathlib import Path

HOME      = Path.home()
WORKSPACE = HOME / "SuneelWorkSpace"
ADWI_DIR  = WORKSPACE / "adwi"
SIMEVAL   = ADWI_DIR / "logs" / "simeval"
LOOP_DIR  = ADWI_DIR / "notes" / "e2e-auto-loop"

PID_FILE    = LOOP_DIR / "running.pid"
CANCEL_FILE = LOOP_DIR / "cancel"
STATUS_FILE = LOOP_DIR / "status.json"

VENV_PY = ADWI_DIR / ".venv" / "bin" / "python3"
RUN_P1  = SIMEVAL / "run_large_eval.py"
RUN_P2  = SIMEVAL / "run_large_eval_p2.py"

TIMEOUT_P1  = 2400   # 40 min per P1 eval
TIMEOUT_P2  = 1200   # 20 min per P2 eval
TIMEOUT_JOB = 14400  # 4 hr overall max

PATCHABLE_FILES = [
    ADWI_DIR / "adwi_cli.py",
    SIMEVAL  / "run_large_eval.py",
    SIMEVAL  / "run_large_eval_p2.py",
    ADWI_DIR / "capabilities.json",
]

# Deterministic known regex fixes (Hybrid Option C, Phase A).
# Initially empty — populate after reviewing cycle-1 failure report.
# Format per entry:
#   id: str
#   description: str
#   target_intents: list[str]   — skip if none of these are currently failing
#   target_file: str            — relative to WORKSPACE
#   check_pattern: str          — regex that must match current file (idempotency guard)
#   old_str: str                — exact string to find and replace (one occurrence)
#   new_str: str                — replacement
KNOWN_REGEX_FIXES: list[dict] = []


# ── Timestamps ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# ── Lock ───────────────────────────────────────────────────────────────────────

def _acquire_lock() -> bool:
    """Try to own running.pid. Returns True if acquired."""
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)       # signal 0: check existence
            return False          # alive — another loop running
        except (ValueError, ProcessLookupError):
            pass                  # stale lock — overwrite
        except PermissionError:
            return False          # process alive, not ours
    PID_FILE.write_text(str(os.getpid()))
    return True


def _release_lock() -> None:
    PID_FILE.unlink(missing_ok=True)


# ── Status writer ──────────────────────────────────────────────────────────────

def _write_status(job_id: str, status: str, cycle: int, max_cycles: int,
                  target: float, extra: dict | None = None) -> None:
    data: dict = {
        "job_id":      job_id,
        "status":      status,
        "updated_at":  _now(),
        "target":      target,
        "max_cycles":  max_cycles,
        "cycle":       cycle,
        "report_path": str(LOOP_DIR / job_id),
    }
    if extra:
        data.update(extra)
    STATUS_FILE.write_text(json.dumps(data, indent=2))


# ── Metrics ────────────────────────────────────────────────────────────────────

def _load_results(session_dir: Path) -> list[dict]:
    rj = session_dir / "results.jsonl"
    if not rj.exists():
        return []
    results: list[dict] = []
    for line in rj.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            results.append(json.loads(line))
    return results


def _compute_metrics(p1_dir: Path, p2_dir: Path) -> dict:
    """
    Combined = dedup-merge P1+P2 on prompt.lower().strip() (P1 first).
    Authoritative formula: matches generate_master_report.py deduplicate().
    Returns p1_total/passed/pct, p2_total/passed/pct, combined_*, fail_by_intent, top_misroutes.
    """
    p1 = _load_results(p1_dir)
    p2 = _load_results(p2_dir)

    def _rate(rs: list[dict]) -> tuple[int, int, float]:
        total  = len(rs)
        passed = sum(1 for r in rs if r["verdict"] == "pass")
        pct    = round(100 * passed / total, 1) if total else 0.0
        return total, passed, pct

    p1_total, p1_passed, p1_pct = _rate(p1)
    p2_total, p2_passed, p2_pct = _rate(p2)

    seen: set[str] = set()
    combined: list[dict] = []
    for r in p1 + p2:
        key = r["prompt"].lower().strip()
        if key not in seen:
            seen.add(key)
            combined.append(r)

    c_total, c_passed, c_pct = _rate(combined)

    failed = [r for r in combined if r["verdict"] == "fail"]
    fail_by_intent: dict[str, int] = {}
    misroutes: dict[str, int] = {}
    for r in failed:
        exp = r.get("expected_intent") or "__none__"
        got = r.get("got_intent")      or "__none__"
        fail_by_intent[exp] = fail_by_intent.get(exp, 0) + 1
        misroutes[f"{exp} → {got}"] = misroutes.get(f"{exp} → {got}", 0) + 1

    return {
        "p1_total":        p1_total,   "p1_passed":    p1_passed,   "p1_pct":    p1_pct,
        "p2_total":        p2_total,   "p2_passed":    p2_passed,   "p2_pct":    p2_pct,
        "combined_total":  c_total,    "combined_passed": c_passed, "combined_pct": c_pct,
        "fail_by_intent":  dict(sorted(fail_by_intent.items(), key=lambda x: -x[1])[:20]),
        "top_misroutes":   dict(sorted(misroutes.items(),      key=lambda x: -x[1])[:10]),
    }


def _find_latest_session(prefix: str) -> Path | None:
    dirs = sorted(SIMEVAL.glob(f"{prefix}-*"))
    return dirs[-1] if dirs else None


# ── Preflight ──────────────────────────────────────────────────────────────────

def _run_preflight(job_dir: Path) -> tuple[bool, str]:
    """py_compile patchable Python files + run test_nlu_regex.py. Returns (ok, detail)."""
    errors: list[str] = []

    for pf in PATCHABLE_FILES:
        if not pf.exists() or pf.suffix != ".py":
            continue
        r = subprocess.run(
            [sys.executable, "-m", "py_compile", str(pf)],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            errors.append(f"py_compile {pf.name}: {r.stderr.strip()}")

    test_file = ADWI_DIR / "simlab" / "tests" / "test_nlu_regex.py"
    if test_file.exists():
        r = subprocess.run(
            [sys.executable, "-m", "unittest", str(test_file)],
            capture_output=True, text=True, cwd=str(WORKSPACE)
        )
        if r.returncode != 0:
            errors.append(f"test_nlu_regex.py FAILED:\n{r.stderr[-2000:]}")

    detail = "\n".join(errors) if errors else "all OK"
    return (not errors, detail)


# ── Dirty worktree guard ───────────────────────────────────────────────────────

def _check_dirty_patchable(snapshots_dir: Path) -> list[str]:
    """
    Return relative paths of patchable files with uncommitted user changes
    NOT made by this job (our own patches are in snapshots_dir as *.bak).
    """
    r = subprocess.run(
        ["git", "status", "--short"],
        capture_output=True, text=True, cwd=str(WORKSPACE)
    )
    our_snaps: set[str] = set()
    if snapshots_dir.exists():
        our_snaps = {f.stem for f in snapshots_dir.glob("*.bak")}

    dirty: list[str] = []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        flags = line[:2].strip()
        fpath = line[3:].strip()
        if not flags:
            continue
        for pf in PATCHABLE_FILES:
            rel = str(pf.relative_to(WORKSPACE))
            if rel == fpath or fpath == pf.name:
                if pf.name not in our_snaps:
                    dirty.append(fpath)
                break
    return dirty


# ── Patch helpers ──────────────────────────────────────────────────────────────

def _snapshot_file(pf: Path, snapshots_dir: Path) -> Path:
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    bak = snapshots_dir / f"{pf.name}.bak"
    shutil.copy2(str(pf), str(bak))
    return bak


def _rollback_file(pf: Path, bak: Path) -> None:
    shutil.copy2(str(bak), str(pf))


def _apply_known_fixes(
    job_dir: Path, metrics: dict, cycle: int
) -> tuple[list[str], list[str], list[str]]:
    """
    Try KNOWN_REGEX_FIXES in order. Returns (applied, skipped, unfixed_intents).
    Each fix: snapshot → apply → preflight → rollback if regression.
    """
    import re as _re
    applied:  list[str] = []
    skipped:  list[str] = []
    snapshots_dir = job_dir / "snapshots"
    failing_intents = set(metrics.get("fail_by_intent", {}).keys())

    for fix in KNOWN_REGEX_FIXES:
        fid    = fix["id"]
        targets = set(fix.get("target_intents", []))
        if targets and not targets.intersection(failing_intents):
            skipped.append(f"{fid}: no matching failing intents")
            continue

        target_file = WORKSPACE / fix["target_file"]
        if not target_file.exists():
            skipped.append(f"{fid}: target file not found")
            continue

        content = target_file.read_text(encoding="utf-8")
        if fix["old_str"] not in content:
            skipped.append(f"{fid}: old_str not present (already applied or file changed)")
            continue

        check_pat = fix.get("check_pattern", "")
        if check_pat and not _re.search(check_pat, content):
            skipped.append(f"{fid}: check_pattern not found")
            continue

        bak = _snapshot_file(target_file, snapshots_dir)
        target_file.write_text(content.replace(fix["old_str"], fix["new_str"], 1), encoding="utf-8")

        ok, detail = _run_preflight(job_dir)
        if not ok:
            _rollback_file(target_file, bak)
            skipped.append(f"{fid}: rolled back — preflight regressed: {detail[:200]}")
            continue

        applied.append(fid)

    fixed_intents: set[str] = set()
    for fid in applied:
        fix = next(f for f in KNOWN_REGEX_FIXES if f["id"] == fid)
        fixed_intents.update(fix.get("target_intents", []))
    unfixed = sorted(failing_intents - fixed_intents)
    return applied, skipped, unfixed


# ── Finalize ───────────────────────────────────────────────────────────────────

def _finalize(
    job_id: str, job_dir: Path, status: str, cycles: list[dict],
    target: float, max_cycles: int, reason: str,
    final_combined_pct: float | None = None,
    needs_llm_review: bool = False,
    unfixed_clusters: list[str] | None = None,
) -> None:
    final = {
        "job_id":             job_id,
        "status":             status,
        "stop_reason":        reason,
        "target":             target,
        "max_cycles":         max_cycles,
        "final_combined_pct": final_combined_pct,
        "needs_llm_review":   needs_llm_review,
        "unfixed_clusters":   unfixed_clusters or [],
        "cycles":             cycles,
        "finished_at":        _now(),
    }
    (job_dir / "final-report.json").write_text(json.dumps(final, indent=2))
    _write_status(job_id, status, len(cycles), max_cycles, target, {
        "stop_reason":        reason,
        "final_combined_pct": final_combined_pct,
        "needs_llm_review":   needs_llm_review,
        "unfixed_clusters":   unfixed_clusters or [],
        "cycles":             cycles,
    })
    print(f"[e2e-loop] DONE — status={status}  reason={reason}")


# ── Main loop ──────────────────────────────────────────────────────────────────

def main(
    target:     float = 98.0,
    max_cycles: int   = 3,
    dry_run:    bool  = False,
    job_id:     str | None = None,
    workers:    int   = 5,
) -> int:
    """Entry point. Returns 0 on success/dry-run, 1 on failure/abort."""
    if job_id is None:
        job_id = f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    job_dir       = LOOP_DIR / job_id
    snapshots_dir = job_dir / "snapshots"
    job_dir.mkdir(parents=True, exist_ok=True)

    if not _acquire_lock():
        print(json.dumps({"error": "E2E loop already running", "pid_file": str(PID_FILE)}))
        return 1

    _write_status(job_id, "running", 0, max_cycles, target,
                  {"started_at": _now(), "dry_run": dry_run, "workers": workers, "cycles": []})
    print(f"[e2e-loop] Started  job_id={job_id}  target={target}%  max_cycles={max_cycles}  dry_run={dry_run}")

    git_snap = subprocess.run(
        ["git", "status", "--short"], capture_output=True, text=True, cwd=str(WORKSPACE)
    ).stdout
    (job_dir / "git-status-at-start.txt").write_text(git_snap)

    py = str(VENV_PY) if VENV_PY.exists() else sys.executable
    job_start_t       = time.monotonic()
    prev_combined_pct: float | None = None
    all_cycles:        list[dict]   = []

    try:
        for cycle in range(1, max_cycles + 1):
            cycle_t = time.monotonic()
            print(f"\n[e2e-loop] ── CYCLE {cycle}/{max_cycles} ──")
            _write_status(job_id, "running", cycle, max_cycles, target,
                          {"cycles": all_cycles})

            if time.monotonic() - job_start_t > TIMEOUT_JOB:
                _finalize(job_id, job_dir, "timeout", all_cycles, target, max_cycles,
                          "Overall job timeout (14400s) reached")
                return 1

            if CANCEL_FILE.exists():
                CANCEL_FILE.unlink(missing_ok=True)
                _finalize(job_id, job_dir, "cancelled", all_cycles, target, max_cycles,
                          "Cancelled by user")
                return 0

            # ── PREFLIGHT ────────────────────────────────────────────────────
            print("[e2e-loop] Preflight...")
            pf_ok, pf_detail = _run_preflight(job_dir)
            if not pf_ok:
                _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                          f"Preflight failed: {pf_detail}")
                return 1

            if dry_run:
                print("[e2e-loop] DRY-RUN: preflight passed. Eval and patching skipped.")
                rep = {
                    "cycle": cycle, "dry_run": True, "preflight": "pass",
                    "p1_pct": None, "p2_pct": None, "combined_pct": None,
                    "patches_applied": [], "patches_skipped": [],
                    "duration_s": round(time.monotonic() - cycle_t, 1),
                }
                all_cycles.append(rep)
                (job_dir / f"cycle-{cycle}-report.json").write_text(json.dumps(rep, indent=2))
                _finalize(job_id, job_dir, "dry_run_complete", all_cycles, target, max_cycles,
                          "Dry-run: preflight OK, eval skipped")
                return 0

            # ── EVAL P1 ──────────────────────────────────────────────────────
            print(f"[e2e-loop] Running P1 eval (workers={workers}, timeout={TIMEOUT_P1}s)...")
            r1 = subprocess.run(
                [py, str(RUN_P1), "--workers", str(workers)],
                capture_output=True, text=True, timeout=TIMEOUT_P1, cwd=str(WORKSPACE)
            )
            if r1.returncode != 0:
                _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                          f"P1 eval failed rc={r1.returncode}: {r1.stderr[-1000:]}")
                return 1
            p1_dir = _find_latest_session("large")

            # ── EVAL P2 ──────────────────────────────────────────────────────
            print(f"[e2e-loop] Running P2 eval (workers={workers}, timeout={TIMEOUT_P2}s)...")
            r2 = subprocess.run(
                [py, str(RUN_P2), "--workers", str(workers)],
                capture_output=True, text=True, timeout=TIMEOUT_P2, cwd=str(WORKSPACE)
            )
            if r2.returncode != 0:
                _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                          f"P2 eval failed rc={r2.returncode}: {r2.stderr[-1000:]}")
                return 1
            p2_dir = _find_latest_session("large-p2")

            # ── METRICS ──────────────────────────────────────────────────────
            if not p1_dir or not p2_dir:
                _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                          "Could not locate eval session dirs after run")
                return 1
            metrics  = _compute_metrics(p1_dir, p2_dir)
            c_pct    = metrics["combined_pct"]
            print(f"[e2e-loop] P1={metrics['p1_pct']}%  P2={metrics['p2_pct']}%  Combined={c_pct}%  target={target}%")

            # ── MONOTONIC GUARD ───────────────────────────────────────────────
            if prev_combined_pct is not None and c_pct < prev_combined_pct:
                _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                          f"Monotonic safety violation: combined dropped {prev_combined_pct}% → {c_pct}%")
                return 1

            cycle_rep: dict = {
                "cycle": cycle, "preflight": "pass",
                **metrics,
                "patches_applied": [], "patches_skipped": [],
                "needs_llm_review": False, "unfixed_clusters": [],
                "duration_s": 0.0,
            }

            # ── SUCCESS ───────────────────────────────────────────────────────
            if c_pct >= target:
                cycle_rep["duration_s"] = round(time.monotonic() - cycle_t, 1)
                all_cycles.append(cycle_rep)
                (job_dir / f"cycle-{cycle}-report.json").write_text(json.dumps(cycle_rep, indent=2))
                _finalize(job_id, job_dir, "success", all_cycles, target, max_cycles,
                          f"Target reached: {c_pct}% >= {target}%",
                          final_combined_pct=c_pct)
                return 0

            # ── DIRTY WORKTREE GUARD ──────────────────────────────────────────
            dirty = _check_dirty_patchable(snapshots_dir)
            if dirty:
                msg = f"Uncommitted user changes in patchable files: {dirty}"
                cycle_rep.update({"needs_llm_review": True, "stop_reason": msg,
                                  "dirty_files": dirty})
                all_cycles.append(cycle_rep)
                (job_dir / f"cycle-{cycle}-report.json").write_text(json.dumps(cycle_rep, indent=2))
                _finalize(job_id, job_dir, "needs_llm_review", all_cycles, target, max_cycles,
                          msg, needs_llm_review=True,
                          unfixed_clusters=sorted(metrics.get("fail_by_intent", {}).keys()))
                return 0

            # ── AUTO-FIX Phase A ──────────────────────────────────────────────
            if KNOWN_REGEX_FIXES:
                print("[e2e-loop] Applying known regex fixes (Phase A)...")
                applied, skipped_fixes, unfixed = _apply_known_fixes(job_dir, metrics, cycle)
                cycle_rep["patches_applied"] = applied
                cycle_rep["patches_skipped"] = skipped_fixes
                if applied:
                    pf_ok2, pf_detail2 = _run_preflight(job_dir)
                    if not pf_ok2:
                        for pf in PATCHABLE_FILES:
                            bak = snapshots_dir / f"{pf.name}.bak"
                            if bak.exists():
                                _rollback_file(pf, bak)
                        _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                                  f"Post-patch preflight failed: {pf_detail2}")
                        return 1
            else:
                unfixed = sorted(metrics.get("fail_by_intent", {}).keys())

            # Phase B: LLM review report
            if c_pct < target:
                cycle_rep["needs_llm_review"] = True
                cycle_rep["unfixed_clusters"]  = unfixed[:20]

            prev_combined_pct           = c_pct
            cycle_rep["duration_s"]     = round(time.monotonic() - cycle_t, 1)
            all_cycles.append(cycle_rep)
            (job_dir / f"cycle-{cycle}-report.json").write_text(json.dumps(cycle_rep, indent=2))

        # ── MAX CYCLES ────────────────────────────────────────────────────────
        final_pct    = all_cycles[-1].get("combined_pct") if all_cycles else None
        needs_review = final_pct is None or final_pct < target
        _finalize(job_id, job_dir, "max_cycles_reached", all_cycles, target, max_cycles,
                  f"Max cycles ({max_cycles}) reached. Final combined: {final_pct}%",
                  final_combined_pct=final_pct, needs_llm_review=needs_review,
                  unfixed_clusters=all_cycles[-1].get("unfixed_clusters", []) if all_cycles else [])
        return 0

    except subprocess.TimeoutExpired as exc:
        _finalize(job_id, job_dir, "timeout", all_cycles, target, max_cycles, str(exc))
        return 1
    except KeyboardInterrupt:
        _finalize(job_id, job_dir, "cancelled", all_cycles, target, max_cycles, "KeyboardInterrupt")
        return 0
    except Exception as exc:
        import traceback
        _finalize(job_id, job_dir, "failed", all_cycles, target, max_cycles,
                  f"Unexpected error: {exc}\n{traceback.format_exc()[-2000:]}")
        return 1
    finally:
        _release_lock()


# ── CLI entry ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Adwi E2E Auto Loop")
    ap.add_argument("--target",     type=float, default=98.0)
    ap.add_argument("--max-cycles", type=int,   default=3)
    ap.add_argument("--dry-run",    action="store_true")
    ap.add_argument("--job-id",     type=str,   default=None)
    ap.add_argument("--workers",    type=int,   default=5)
    args = ap.parse_args()
    sys.exit(main(
        target=args.target, max_cycles=args.max_cycles,
        dry_run=args.dry_run, job_id=args.job_id, workers=args.workers,
    ))
```

- [ ] **Step 2: Verify syntax**

```bash
cd /Users/MAC/SuneelWorkSpace
python3 -m py_compile adwi/e2e_auto_loop.py && echo "syntax OK"
```
Expected: `syntax OK`

---

### Task 2: `adwi/bin/adwi-e2e-status-reader` — Read-only status helper

**Files:**
- Create: `adwi/bin/adwi-e2e-status-reader`

**Interfaces:**
- Consumes: `adwi/notes/e2e-auto-loop/status.json` (Task 1 output)
- Consumes: `adwi/notes/e2e-auto-loop/<job_id>/final-report.json` (Task 1 output)
- Produces: stdout — valid JSON only, no secrets read

- [ ] **Step 1: Create `adwi/bin/adwi-e2e-status-reader`**

```python
#!/usr/bin/env python3
"""
Adwi E2E Auto Loop — read-only status/report/cancel helper.
Prints valid JSON only. Never reads secrets.
Usage: adwi-e2e-status-reader [--status | --report | --cancel]
"""
import json, os, sys
from pathlib import Path

HOME     = Path.home()
LOOP_DIR = HOME / "SuneelWorkSpace" / "adwi" / "notes" / "e2e-auto-loop"
STATUS_F = LOOP_DIR / "status.json"
CANCEL_F = LOOP_DIR / "cancel"

_NO_JOB = {"status": "no_job", "message": "No E2E auto loop has ever run on this machine."}


def _cmd_status() -> None:
    if not STATUS_F.exists():
        print(json.dumps(_NO_JOB))
        return
    print(STATUS_F.read_text(encoding="utf-8"))


def _cmd_report() -> None:
    if not STATUS_F.exists():
        print(json.dumps(_NO_JOB))
        return
    try:
        status = json.loads(STATUS_F.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"error": f"Cannot parse status.json: {exc}"}))
        return

    job_id  = status.get("job_id")
    job_dir = LOOP_DIR / job_id if job_id else None

    if job_dir and (job_dir / "final-report.json").exists():
        print((job_dir / "final-report.json").read_text(encoding="utf-8"))
        return

    if job_dir:
        cycles = sorted(job_dir.glob("cycle-*-report.json"))
        if cycles:
            print(cycles[-1].read_text(encoding="utf-8"))
            return

    print(json.dumps({"status": status.get("status", "unknown"),
                      "message": "No cycle reports yet — loop may be starting."}))


def _cmd_cancel() -> None:
    LOOP_DIR.mkdir(parents=True, exist_ok=True)
    CANCEL_F.write_text("cancel")
    print(json.dumps({"ok": True, "cancel_requested": True,
                      "message": "Cancel sentinel written. Loop will stop after current operation."}))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if mode == "--status":
        _cmd_status()
    elif mode == "--report":
        _cmd_report()
    elif mode == "--cancel":
        _cmd_cancel()
    else:
        print(json.dumps({"error": f"Unknown mode: {mode}. Use --status, --report, or --cancel."}))
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable and verify syntax**

```bash
chmod +x /Users/MAC/SuneelWorkSpace/adwi/bin/adwi-e2e-status-reader
python3 -m py_compile /Users/MAC/SuneelWorkSpace/adwi/bin/adwi-e2e-status-reader && echo "syntax OK"
```
Expected: `syntax OK`

---

### Task 3: `server.py` — Add Popen start route + 3 read-only routes

**Files:**
- Modify: `adwi/services/command-api/server.py`

**Interfaces:**
- Consumes: `adwi/e2e_auto_loop.py` (launched via Popen)
- Consumes: `adwi/bin/adwi-e2e-status-reader` (via subprocess.run, existing pattern)
- Produces: `GET /adwi-e2e-auto-loop-start` — Popen, returns `{job_id, status, pid}` in <1s
- Produces: `GET /adwi-e2e-auto-loop-status` — reads status.json via helper
- Produces: `GET /adwi-e2e-auto-loop-report` — reads latest report via helper
- Produces: `GET /adwi-e2e-auto-loop-cancel` — writes cancel sentinel via helper

- [ ] **Step 1: Add E2E constants after existing VENV_PY/ADWI_CLI lines**

In `adwi/services/command-api/server.py`, after line 29 (`ADWI_CLI = ...`), insert:

```python
E2E_LOOP_PY      = os.path.join(HOME, "SuneelWorkSpace", "adwi", "e2e_auto_loop.py")
E2E_STATUS_READER = os.path.join(HOME, "SuneelWorkSpace", "adwi", "bin", "adwi-e2e-status-reader")
E2E_LOOP_DIR     = Path(HOME) / "SuneelWorkSpace" / "adwi" / "notes" / "e2e-auto-loop"
```

- [ ] **Step 2: Add 3 read-only routes to `ALLOWED_COMMANDS`**

Append to `ALLOWED_COMMANDS` dict (before the closing `}`):

```python
    "/adwi-e2e-auto-loop-status": [VENV_PY, E2E_STATUS_READER, "--status"],
    "/adwi-e2e-auto-loop-report": [VENV_PY, E2E_STATUS_READER, "--report"],
    "/adwi-e2e-auto-loop-cancel": [VENV_PY, E2E_STATUS_READER, "--cancel"],
```

- [ ] **Step 3: Add `_handle_e2e_start` method to `Handler` class**

Add before `def log_message`:

```python
    def _handle_e2e_start(self) -> None:
        """Launch e2e_auto_loop.py as a detached background process. Returns in <1s."""
        pid_file = E2E_LOOP_DIR / "running.pid"
        if pid_file.exists():
            try:
                existing_pid = int(pid_file.read_text().strip())
                os.kill(existing_pid, 0)
                self._send_json(409, {
                    "error": "E2E loop already running",
                    "pid": existing_pid,
                    "status_route": "/adwi-e2e-auto-loop-status"
                })
                return
            except (ValueError, ProcessLookupError):
                pass   # stale lock — proceed
            except PermissionError:
                self._send_json(409, {"error": "E2E loop already running (PermissionError checking PID)"})
                return

        job_id  = f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        job_dir = E2E_LOOP_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        log_path = job_dir / "loop.log"

        try:
            proc = subprocess.Popen(
                [VENV_PY, E2E_LOOP_PY, "--job-id", job_id],
                start_new_session=True,
                stdout=open(str(log_path), "w"),
                stderr=subprocess.STDOUT,
                env={
                    **os.environ,
                    "PATH": f"{BIN}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                    "SUNEEL_COMMAND_API_CONTEXT": "1",
                }
            )
            self._send_json(200, {
                "job_id":       job_id,
                "status":       "started",
                "pid":          proc.pid,
                "log":          str(log_path),
                "status_route": "/adwi-e2e-auto-loop-status",
                "report_route": "/adwi-e2e-auto-loop-report",
            })
        except Exception as exc:
            self._send_json(500, {"error": f"Failed to start E2E loop: {exc}"})
```

- [ ] **Step 4: Route `/adwi-e2e-auto-loop-start` before ALLOWED_COMMANDS lookup in `do_GET`**

In `do_GET`, after the auth check and `"/"` handler but before `if self.path not in ALLOWED_COMMANDS:`, insert:

```python
        if self.path == "/adwi-e2e-auto-loop-start":
            self._handle_e2e_start()
            return
```

- [ ] **Step 5: Verify syntax**

```bash
python3 -m py_compile /Users/MAC/SuneelWorkSpace/adwi/services/command-api/server.py && echo "syntax OK"
```
Expected: `syntax OK`

---

### Task 4: `adwi_cli.py` — Add 4 CLI commands

**Files:**
- Modify: `adwi/adwi_cli.py`

**Interfaces:**
- Consumes: `e2e_auto_loop.main(...)` (lazy import from same directory)
- Consumes: `adwi/notes/e2e-auto-loop/status.json` (direct read for status/report/cancel)
- Produces: CLI commands `/e2e-auto-loop`, `/e2e-auto-loop-status`, `/e2e-auto-loop-report`, `/e2e-auto-loop-cancel`

- [ ] **Step 1: Add 4 `cmd_e2e_*` functions**

Add after the `cmd_nightly_run` function block (search for `def cmd_nightly_run` to find the location):

```python
# ── E2E Auto Loop ──────────────────────────────────────────────────────────────

def cmd_e2e_auto_loop(args: str = "") -> None:
    """Start the E2E auto-loop (NLU eval → analyze → fix → retest)."""
    import argparse as _ap
    p = _ap.ArgumentParser(prog="/e2e-auto-loop", add_help=False)
    p.add_argument("--target",     type=float, default=98.0)
    p.add_argument("--max-cycles", type=int,   default=3)
    p.add_argument("--dry-run",    action="store_true")
    p.add_argument("--workers",    type=int,   default=5)
    p.add_argument("--background", action="store_true")
    try:
        opts, _ = p.parse_known_args(args.split() if args else [])
    except SystemExit:
        return

    pid_file = ADWI_DIR / "notes" / "e2e-auto-loop" / "running.pid"
    if pid_file.exists():
        try:
            existing_pid = int(pid_file.read_text().strip())
            import os as _os
            _os.kill(existing_pid, 0)
            adwi_say(f"E2E loop already running (PID {existing_pid}). Use /e2e-auto-loop-status to check.")
            return
        except (ValueError, ProcessLookupError):
            pass

    if opts.background:
        import subprocess as _sp
        job_id = f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        loop_dir = ADWI_DIR / "notes" / "e2e-auto-loop" / job_id
        loop_dir.mkdir(parents=True, exist_ok=True)
        log_path = loop_dir / "loop.log"
        cmd_args = [
            str(ADWI_DIR / ".venv" / "bin" / "python3"),
            str(ADWI_DIR / "e2e_auto_loop.py"),
            "--job-id", job_id,
            "--target", str(opts.target),
            "--max-cycles", str(opts.max_cycles),
            "--workers", str(opts.workers),
        ]
        if opts.dry_run:
            cmd_args.append("--dry-run")
        _sp.Popen(cmd_args, start_new_session=True,
                  stdout=open(str(log_path), "w"), stderr=_sp.STDOUT)
        adwi_say(f"E2E loop started in background — job_id={job_id}")
        cprint(f"  Log: {log_path}", GRAY)
        cprint(f"  Check: /e2e-auto-loop-status", GRAY)
    else:
        # Foreground
        import sys as _sys
        _sys.path.insert(0, str(ADWI_DIR))
        from e2e_auto_loop import main as _e2e_main
        adwi_head("E2E Auto Loop")
        rc = _e2e_main(
            target=opts.target, max_cycles=opts.max_cycles,
            dry_run=opts.dry_run, workers=opts.workers,
        )
        if rc == 0:
            cprint(f"\n  {GREEN}✓ Loop completed successfully{RESET}", "")
        else:
            cprint(f"\n  {RED}✗ Loop ended with failure — see /e2e-auto-loop-report{RESET}", "")


def cmd_e2e_auto_loop_status() -> None:
    """Show current E2E auto-loop status."""
    loop_dir = ADWI_DIR / "notes" / "e2e-auto-loop"
    status_f = loop_dir / "status.json"
    adwi_head("E2E Auto Loop Status")
    if not status_f.exists():
        cprint("  No E2E loop has ever run on this machine.", GRAY)
        return
    try:
        d = json.loads(status_f.read_text(encoding="utf-8"))
    except Exception as exc:
        cprint(f"  Cannot read status.json: {exc}", RED)
        return
    status = d.get("status", "unknown")
    color  = GREEN if status == "success" else (YELLOW if status in ("running", "dry_run_complete") else RED)
    cprint(f"  Status:      {color}{status}{RESET}", "")
    cprint(f"  Job ID:      {d.get('job_id', '—')}", "")
    cprint(f"  Cycle:       {d.get('cycle', 0)} / {d.get('max_cycles', 3)}", "")
    cprint(f"  Target:      {d.get('target', 98.0)}%", "")
    cprint(f"  Updated:     {d.get('updated_at', '—')}", GRAY)
    if d.get("final_combined_pct") is not None:
        pct   = d["final_combined_pct"]
        color = GREEN if pct >= d.get("target", 98.0) else YELLOW
        cprint(f"  Final combined: {color}{pct}%{RESET}", "")
    if d.get("needs_llm_review"):
        cprint(f"\n  {YELLOW}⚠ Needs LLM review — run /e2e-auto-loop-report for details{RESET}", "")
    if d.get("stop_reason"):
        cprint(f"\n  Stop reason: {d['stop_reason']}", GRAY)


def cmd_e2e_auto_loop_report() -> None:
    """Show the latest E2E auto-loop cycle or final report."""
    loop_dir = ADWI_DIR / "notes" / "e2e-auto-loop"
    status_f = loop_dir / "status.json"
    adwi_head("E2E Auto Loop Report")
    if not status_f.exists():
        cprint("  No E2E loop has ever run on this machine.", GRAY)
        return
    try:
        d       = json.loads(status_f.read_text(encoding="utf-8"))
        job_id  = d.get("job_id")
        job_dir = loop_dir / job_id if job_id else None
    except Exception as exc:
        cprint(f"  Cannot read status.json: {exc}", RED)
        return

    report_file = None
    if job_dir and (job_dir / "final-report.json").exists():
        report_file = job_dir / "final-report.json"
    elif job_dir:
        cycles = sorted(job_dir.glob("cycle-*-report.json"))
        if cycles:
            report_file = cycles[-1]

    if not report_file:
        cprint("  No cycle reports yet — loop may be starting.", GRAY)
        return

    try:
        r = json.loads(report_file.read_text(encoding="utf-8"))
    except Exception as exc:
        cprint(f"  Cannot parse report: {exc}", RED)
        return

    cprint(f"  File: {report_file.name}", GRAY)
    cprint(f"  Status:   {r.get('status', r.get('cycle', '?'))}", "")
    if r.get("combined_pct") is not None:
        cprint(f"  Combined: {r['combined_pct']}%  (P1={r.get('p1_pct')}%  P2={r.get('p2_pct')}%)", BOLD)
    if r.get("fail_by_intent"):
        cprint(f"\n  Top failing intents:", "")
        for intent, count in list(r["fail_by_intent"].items())[:8]:
            cprint(f"    {RED}{intent}{RESET}: {count}", "")
    if r.get("unfixed_clusters"):
        cprint(f"\n  Unfixed clusters (need LLM review): {r['unfixed_clusters'][:10]}", YELLOW)
    if r.get("patches_applied"):
        cprint(f"\n  Patches applied: {r['patches_applied']}", GREEN)
    if r.get("stop_reason"):
        cprint(f"\n  Stop reason: {r['stop_reason']}", GRAY)


def cmd_e2e_auto_loop_cancel() -> None:
    """Cancel a running E2E auto-loop job."""
    loop_dir    = ADWI_DIR / "notes" / "e2e-auto-loop"
    cancel_file = loop_dir / "cancel"
    pid_file    = loop_dir / "running.pid"
    adwi_head("E2E Auto Loop Cancel")

    if not pid_file.exists():
        cprint("  No E2E loop is currently running.", GRAY)
        return

    loop_dir.mkdir(parents=True, exist_ok=True)
    cancel_file.write_text("cancel")
    cprint(f"  {GREEN}✓ Cancel sentinel written{RESET} — loop will stop after current operation.", "")
    cprint(f"  Check: /e2e-auto-loop-status", GRAY)
```

- [ ] **Step 2: Add dispatch lines**

In the main `dispatch_command()` dispatch block, after the `# ── Nightly improvement ──` section, add:

```python
    # ── E2E Auto Loop ──
    elif line.startswith("/e2e-auto-loop "):  cmd_e2e_auto_loop(line[15:].strip())
    elif line == "/e2e-auto-loop":            cmd_e2e_auto_loop()
    elif line == "/e2e-auto-loop-status":     cmd_e2e_auto_loop_status()
    elif line == "/e2e-auto-loop-report":     cmd_e2e_auto_loop_report()
    elif line == "/e2e-auto-loop-cancel":     cmd_e2e_auto_loop_cancel()
```

- [ ] **Step 3: Add help text**

In the `/help` block (search for `"/nightly-run"`), add after the nightly entries:

```python
  /e2e-auto-loop             Start NLU eval→fix→retest loop (--target 98 --max-cycles 3)
  /e2e-auto-loop --dry-run   Preflight only, no eval, safe test of loop control flow
  /e2e-auto-loop-status      Show current/last loop job status
  /e2e-auto-loop-report      Show latest cycle or final report
  /e2e-auto-loop-cancel      Cancel a running loop job
```

- [ ] **Step 4: Verify syntax**

```bash
python3 -m py_compile /Users/MAC/SuneelWorkSpace/adwi/adwi_cli.py && echo "syntax OK"
```
Expected: `syntax OK`

---

### Task 5: Home Assistant YAML + n8n workflow

**Files:**
- Modify: `adwi/infra/docker/homeassistant-data/configuration.yaml`
- Modify: `adwi/infra/docker/homeassistant-data/ui-lovelace.yaml`
- Create: `adwi/automation/workflows/adwi-e2e-auto-loop.json`

- [ ] **Step 1: Add 2 `rest_command` entries to `configuration.yaml`**

After the existing `adwi_brief:` block, add:

```yaml
  adwi_e2e_auto_loop:
    url: "http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop"
    method: POST
    content_type: "application/json"
    payload: '{"command": "e2e-auto-loop"}'
  adwi_e2e_auto_loop_status:
    url: "http://100.110.47.128:5678/webhook/adwi-e2e-auto-loop-status"
    method: POST
    content_type: "application/json"
    payload: '{"command": "e2e-auto-loop-status"}'
```

No secrets hardcoded. Secret stays in n8n env var only.

- [ ] **Step 2: Add 2 buttons to `ui-lovelace.yaml`**

In the `type: grid` card's `cards:` list, after the last existing button, add:

```yaml
          - type: button
            name: E2E Auto Loop
            icon: mdi:refresh-auto
            tap_action:
              action: call-service
              service: rest_command.adwi_e2e_auto_loop
            hold_action:
              action: call-service
              service: notify.mobile_app_the_suns_iphone
              service_data:
                title: "Adwi E2E Loop"
                message: "E2E Auto Loop started — check /e2e-auto-loop-status for progress"
                data:
                  push:
                    sound: default

          - type: button
            name: E2E Loop Status
            icon: mdi:chart-line
            tap_action:
              action: call-service
              service: rest_command.adwi_e2e_auto_loop_status
```

- [ ] **Step 3: Create `adwi/automation/workflows/adwi-e2e-auto-loop.json`**

```json
{
  "name": "Adwi — E2E Auto Loop",
  "nodes": [
    {
      "parameters": {},
      "id": "manual-trigger",
      "name": "Manual Test Trigger",
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "adwi-e2e-auto-loop",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook-trigger",
      "name": "Webhook — E2E Auto Loop",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [0, 200],
      "webhookId": "adwi-e2e-auto-loop"
    },
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "adwi-e2e-auto-loop-status",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook-status",
      "name": "Webhook — E2E Status",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [0, 400],
      "webhookId": "adwi-e2e-auto-loop-status"
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://host.docker.internal:5055/adwi-e2e-auto-loop-start",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Adwi-Secret",
              "value": "={{ $env.ADWI_LOCAL_SECRET }}"
            }
          ]
        },
        "sendBody": false,
        "options": { "timeout": 10000 }
      },
      "id": "call-e2e-start",
      "name": "Start E2E Loop",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [320, 100]
    },
    {
      "parameters": {
        "method": "GET",
        "url": "http://host.docker.internal:5055/adwi-e2e-auto-loop-status",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Adwi-Secret",
              "value": "={{ $env.ADWI_LOCAL_SECRET }}"
            }
          ]
        },
        "sendBody": false,
        "options": { "timeout": 10000 }
      },
      "id": "call-e2e-status",
      "name": "Get E2E Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [320, 400]
    },
    {
      "parameters": {
        "jsCode": "// Extract job_id and status from Safe Command API envelope.\n// Do NOT log the X-Adwi-Secret value.\nconst env = $input.item.json;\nconst raw = (env.stdout || '').trim();\nif (!raw) return { ok: false, error: 'Empty stdout from /adwi-e2e-auto-loop-start' };\ntry {\n  const result = JSON.parse(raw);\n  return {\n    ok: true,\n    job_id: result.job_id || env.job_id || 'unknown',\n    status: result.status || 'started',\n    pid: result.pid || null,\n    status_route: '/adwi-e2e-auto-loop-status'\n  };\n} catch (e) {\n  // start route may return JSON directly (not wrapped)\n  return { ok: true, raw_response: String(raw).slice(0, 500) };\n}"
      },
      "id": "parse-start-result",
      "name": "Parse Start Result",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [640, 100]
    },
    {
      "parameters": {
        "jsCode": "// Extract status from Safe Command API envelope.\nconst env = $input.item.json;\nconst raw = (env.stdout || '').trim();\nif (!raw) return { ok: false, error: 'Empty stdout' };\ntry {\n  const s = JSON.parse(raw);\n  return {\n    ok: true,\n    job_id: s.job_id || null,\n    status: s.status || null,\n    combined_pct: s.final_combined_pct || null,\n    needs_llm_review: s.needs_llm_review || false,\n    cycle: s.cycle || 0,\n    max_cycles: s.max_cycles || 3,\n    updated_at: s.updated_at || null\n  };\n} catch (e) {\n  return { ok: false, error: String(e), raw: String(raw).slice(0, 200) };\n}"
      },
      "id": "parse-status-result",
      "name": "Parse Status Result",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [640, 400]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify($json) }}"
      },
      "id": "respond-start",
      "name": "Respond to HA (start)",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [960, 100]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ JSON.stringify($json) }}"
      },
      "id": "respond-status",
      "name": "Respond to HA (status)",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [960, 400]
    }
  ],
  "connections": {
    "Manual Test Trigger":      { "main": [[{ "node": "Start E2E Loop",  "type": "main", "index": 0 }]] },
    "Webhook — E2E Auto Loop":  { "main": [[{ "node": "Start E2E Loop",  "type": "main", "index": 0 }]] },
    "Webhook — E2E Status":     { "main": [[{ "node": "Get E2E Status",  "type": "main", "index": 0 }]] },
    "Start E2E Loop":           { "main": [[{ "node": "Parse Start Result", "type": "main", "index": 0 }]] },
    "Get E2E Status":           { "main": [[{ "node": "Parse Status Result", "type": "main", "index": 0 }]] },
    "Parse Start Result":       { "main": [[{ "node": "Respond to HA (start)",  "type": "main", "index": 0 }]] },
    "Parse Status Result":      { "main": [[{ "node": "Respond to HA (status)", "type": "main", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" },
  "notes": "Adwi E2E Auto Loop workflow. Requires ADWI_LOCAL_SECRET set in n8n environment variables. Import via Settings → Workflows → Import. Do NOT log X-Adwi-Secret values in execution logs. Webhook URLs: POST /webhook/adwi-e2e-auto-loop (start), POST /webhook/adwi-e2e-auto-loop-status (status check). The Start node uses a 10s timeout — the loop itself runs in background on Mac.",
  "active": false
}
```

---

### Task 6: `adwi/docs/E2E_AUTO_LOOP.md`

**Files:**
- Create: `adwi/docs/E2E_AUTO_LOOP.md`

- [ ] **Step 1: Create documentation file** (see content in implementation — covers architecture, lock model, metric formula, dirty-worktree protection, stop conditions, manual steps, troubleshooting)

---

### Task 7: Verification

**Files:** none (read-only checks)

- [ ] **Step 1: Syntax checks**

```bash
cd /Users/MAC/SuneelWorkSpace
python3 -m py_compile adwi/e2e_auto_loop.py           && echo "e2e_auto_loop OK"
python3 -m py_compile adwi/services/command-api/server.py && echo "server OK"
python3 -m py_compile adwi/adwi_cli.py                && echo "adwi_cli OK"
python3 -m py_compile adwi/bin/adwi-e2e-status-reader && echo "status-reader OK"
```
Expected: all four print OK.

- [ ] **Step 2: Unit tests**

```bash
python3 -m unittest adwi/simlab/tests/test_nlu_regex.py 2>&1 | tail -3
```
Expected: `OK` with no failures.

- [ ] **Step 3: CLI status (no job running)**

```bash
python3 adwi/adwi_cli.py /e2e-auto-loop-status
```
Expected: prints "No E2E loop has ever run on this machine." (or similar — no crash).

- [ ] **Step 4: Dry-run test**

```bash
python3 adwi/adwi_cli.py /e2e-auto-loop --target 98 --max-cycles 1 --dry-run
```
Expected: prints `[e2e-loop] Started`, runs preflight, prints `DRY-RUN: preflight passed. Eval and patching skipped.`, writes status.json and cycle-1-report.json, exits 0. No eval, no patches.

- [ ] **Step 5: Verify status.json was written**

```bash
cat adwi/notes/e2e-auto-loop/status.json
```
Expected: JSON with `"status": "dry_run_complete"`.

- [ ] **Step 6: Test status-reader directly**

```bash
python3 adwi/bin/adwi-e2e-status-reader --status
python3 adwi/bin/adwi-e2e-status-reader --report
```
Expected: valid JSON printed for both.

- [ ] **Step 7: Test Safe Command API — unauthorized**

```bash
curl -s http://127.0.0.1:5055/adwi-e2e-auto-loop-status
```
Expected: `{"error": "Unauthorized — X-Adwi-Secret header required"}` (401 if secret is set).

- [ ] **Step 8: Document authorized API test**

Authorized test requires `X-Adwi-Secret` — do NOT pass the secret in shell history. Manual test:
```bash
# In a terminal where ADWI_LOCAL_SECRET is already in your env:
curl -s -H "X-Adwi-Secret: $ADWI_LOCAL_SECRET" http://127.0.0.1:5055/adwi-e2e-auto-loop-status
```
Expected: JSON status output. Do NOT hardcode the secret in any file or script.
