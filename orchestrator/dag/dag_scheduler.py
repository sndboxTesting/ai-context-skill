#!/usr/bin/env python3
"""P3.5 — Manage cron-style schedule registry for DAG pipelines."""

import json
import sys
from datetime import datetime
from pathlib import Path

REGISTRY_PATH = Path(__file__).parent / "schedule_registry.json"
PIPELINES_DIR = Path(__file__).parent / "pipelines"


def _load() -> dict:
    if not REGISTRY_PATH.exists():
        return {}
    return json.loads(REGISTRY_PATH.read_text())


def _save(registry: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))


def _parse_cron(expr: str) -> tuple[str, str, str, str, str]:
    """Return (minute, hour, dom, month, dow) tuple."""
    parts = expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expr!r}")
    return tuple(parts)  # type: ignore


def _cron_matches(expr: str, now: datetime) -> bool:
    """Check if cron expression matches the current time (minute-level precision)."""
    try:
        minute, hour, dom, month, dow = _parse_cron(expr)
    except ValueError:
        return False

    def _match(field: str, val: int) -> bool:
        if field == "*":
            return True
        try:
            return int(field) == val
        except ValueError:
            return False

    return (
        _match(minute, now.minute)
        and _match(hour, now.hour)
        and _match(dom, now.day)
        and _match(month, now.month)
        and _match(dow, now.weekday())
    )


def list_schedules() -> None:
    registry = _load()
    if not registry:
        print("No scheduled pipelines.")
        return
    print(f"{'Pipeline':<30} {'Schedule':<20} {'Last run'}")
    print(f"{'-'*30} {'-'*20} {'-'*20}")
    for name, entry in registry.items():
        print(f"{name:<30} {entry['schedule']:<20} {entry.get('last_run','never')}")


def add_schedule(pipeline_yaml: str, schedule: str) -> None:
    path = Path(pipeline_yaml)
    if not path.exists():
        print(f"ERROR: {pipeline_yaml} not found"); sys.exit(1)
    _parse_cron(schedule)  # validate

    try:
        import yaml  # type: ignore
        pipeline = yaml.safe_load(path.read_text())
        name = pipeline.get("name", path.stem)
    except Exception:
        name = path.stem

    registry = _load()
    registry[name] = {
        "pipeline": str(path.resolve()),
        "schedule": schedule,
        "added_at": datetime.now().isoformat(),
        "last_run": None,
    }
    _save(registry)
    print(f"Scheduled: {name} @ {schedule}")


def remove_schedule(pipeline_name: str) -> None:
    registry = _load()
    if pipeline_name not in registry:
        print(f"Not found: {pipeline_name}"); sys.exit(1)
    del registry[pipeline_name]
    _save(registry)
    print(f"Removed: {pipeline_name}")


def run_due() -> None:
    """Run all pipelines whose cron schedule matches now. Called by daily evolution."""
    registry = _load()
    now = datetime.now()
    ran = 0
    for name, entry in registry.items():
        if _cron_matches(entry["schedule"], now):
            print(f"Running due pipeline: {name}")
            from dag_runner import run
            run(entry["pipeline"])
            registry[name]["last_run"] = now.isoformat()
            ran += 1
    _save(registry)
    print(f"{ran} pipeline(s) ran.")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Manage pipeline schedules")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--add", metavar="PIPELINE_YAML")
    group.add_argument("--remove", metavar="PIPELINE_NAME")
    group.add_argument("--run-due", action="store_true")
    parser.add_argument("--schedule", default=None)
    args = parser.parse_args()

    if args.list:
        list_schedules()
    elif args.add:
        if not args.schedule:
            print("--schedule required with --add"); sys.exit(1)
        add_schedule(args.add, args.schedule)
    elif args.remove:
        remove_schedule(args.remove)
    elif args.run_due:
        run_due()


if __name__ == "__main__":
    main()
