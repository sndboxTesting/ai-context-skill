"""
commands/eval.py — Eval, routing inspection, backup status, and watcher commands.

All commands in this module are read-only inspection / status checks.
They are safe to route through registry-first dispatch (Phase 2).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adwi.command_registry import CommandRegistry


def _cli():
    import importlib.util
    from pathlib import Path
    if "adwi_cli" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "adwi_cli",
            Path(__file__).parent.parent / "adwi_cli.py",
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules["adwi_cli"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return sys.modules["adwi_cli"]


# ── Handlers ──────────────────────────────────────────────────────────────────


def _eval_routing(args: str, ctx: dict) -> None:
    _cli().cmd_eval_routing()


def _test_adwi(args: str, ctx: dict) -> None:
    _cli().cmd_test_adwi()


def _backup_status(args: str, ctx: dict) -> None:
    _cli().cmd_backup_status()


def _backup_log(args: str, ctx: dict) -> None:
    _cli().cmd_backup_log()


def _backup_audit(args: str, ctx: dict) -> None:
    _cli().cmd_backup_audit()


def _route(args: str, ctx: dict) -> None:
    _cli().cmd_route(args)


def _watcher_status(args: str, ctx: dict) -> None:
    _cli().run_cmd("watcher", ["status-openwebui-knowledge-watcher"])


def _eval_adwi(args: str, ctx: dict) -> None:
    _cli().cmd_eval_adwi()


def _export_training_example(args: str, ctx: dict) -> None:
    _cli().cmd_export_training_example(args)


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/eval-routing",
        description="Run NLU routing eval against the full scenario set",
        category="eval",
        intents=["eval_routing"],
    )(_eval_routing)

    registry.register(
        "/test-adwi",
        description="Run the full Adwi test suite",
        category="eval",
        intents=["test_adwi"],
    )(_test_adwi)

    registry.register(
        "/backup-status",
        description="Show git backup health and last-run timestamp",
        category="system",
        intents=["backup_status"],
    )(_backup_status)

    registry.register(
        "/backup-log",
        description="Show recent git backup log entries",
        category="system",
    )(_backup_log)

    registry.register(
        "/backup-audit",
        description="Audit all git backup metadata and verify integrity",
        category="system",
    )(_backup_audit)

    registry.register(
        "/route",
        description="Show or test the current NLU routing configuration",
        category="system",
        args_schema={"query": "str?"},
    )(_route)

    registry.register(
        "/watcher-status",
        description="Check Open WebUI knowledge watcher service status",
        category="system",
    )(_watcher_status)

    registry.register(
        "/eval-adwi",
        description="Run the full Adwi capability evaluation",
        category="eval",
        intents=["eval_adwi"],
    )(_eval_adwi)

    registry.register(
        "/export-training-example",
        description="Export a labeled training example from the last interaction",
        category="eval",
        intents=["export_training"],
        args_schema={"query": "str?"},
    )(_export_training_example)
