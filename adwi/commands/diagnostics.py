"""
commands/diagnostics.py — System visibility, model listing, MCP status, trace logs.

All commands in this module are read-only inspection / reporting commands.
They are safe to route through registry-first dispatch (Phase 3).
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


def _models(args: str, ctx: dict) -> None:
    _cli()._list_models()


def _mcp(args: str, ctx: dict) -> None:
    _cli().cmd_mcp_status()


def _inspect_system(args: str, ctx: dict) -> None:
    _cli().cmd_inspect_system()


def _trusted_roots(args: str, ctx: dict) -> None:
    _cli().cmd_trusted_roots()


def _tool_roadmap(args: str, ctx: dict) -> None:
    _cli().cmd_tool_roadmap()


def _trace_log(args: str, ctx: dict) -> None:
    _cli().cmd_trace_log(int(args) if args.isdigit() else 0)


def _training_plan(args: str, ctx: dict) -> None:
    _cli().cmd_training_plan()


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/models",
        description="List available local Ollama models",
        category="system",
    )(_models)

    registry.register(
        "/mcp",
        description="Show configured MCP tool servers with live-service check",
        category="system",
    )(_mcp)

    registry.register(
        "/inspect-system",
        description="Full read-only inventory of the local AI system (saves report)",
        category="system",
    )(_inspect_system)

    registry.register(
        "/trusted-roots",
        description="Show current trusted read roots",
        category="system",
        intents=["trusted_roots"],
    )(_trusted_roots)

    registry.register(
        "/tool-roadmap",
        description="Show Phase 5 tool stack roadmap with install status",
        category="system",
        intents=["tool_roadmap"],
    )(_tool_roadmap)

    registry.register(
        "/trace-log",
        description="Show recent activity trace log (optional: N for nth most recent)",
        category="system",
        args_schema={"n": "int?"},
    )(_trace_log)

    registry.register(
        "/training-plan",
        description="Show training data status and fine-tuning readiness",
        category="system",
    )(_training_plan)
