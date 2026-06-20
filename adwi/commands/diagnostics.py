"""
commands/diagnostics.py — System visibility, model listing, MCP status, trace logs,
and diagnostic/repair commands.

All commands in this module are read-only inspection / reporting or bounded
local-only repair/viewer commands. No network calls, no external API, no git.
Safe to route through registry-first dispatch (Phases 3 + 23).
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


# ── Handlers — Phase 3 (original) ─────────────────────────────────────────────


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


# ── Handlers — Phase 23 (diagnostics + viewer cluster) ────────────────────────


def _capability_audit(args: str, ctx: dict) -> None:
    _cli().cmd_capability_audit()


def _memory_curate(args: str, ctx: dict) -> None:
    _cli().cmd_memory_curate()


def _mcp_setup(args: str, ctx: dict) -> None:
    _cli().cmd_mcp_setup()


def _repair_adwi(args: str, ctx: dict) -> None:
    _cli().cmd_repair_adwi()


def _run_safe(args: str, ctx: dict) -> None:
    _cli().cmd_run_safe(args)


def _learn_from_last_error(args: str, ctx: dict) -> None:
    _cli().cmd_learn_from_last_error()


def _secrets_status(args: str, ctx: dict) -> None:
    _cli().run_cmd("secrets", ["adwi-secrets-status"])


def _journal(args: str, ctx: dict) -> None:
    cli = _cli()
    if cli.JOURNAL_FILE.exists():
        print("\n".join(cli.JOURNAL_FILE.read_text(encoding="utf-8").splitlines()[-60:]))


def _mistakes(args: str, ctx: dict) -> None:
    cli = _cli()
    if cli.MISTAKES_FILE.exists():
        print("\n".join(cli.MISTAKES_FILE.read_text(encoding="utf-8").splitlines()[-60:]))


def _nightly_log(args: str, ctx: dict) -> None:
    _cli().cmd_nightly_log(int(args) if args.isdigit() else 0)


def _inspect_code(args: str, ctx: dict) -> None:
    if not args:
        print("  Usage: /inspect-code <file-path>")
        return
    _cli().cmd_inspect_code(args)


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    # Phase 3 — original entries
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
        description="Show recent activity trace log (optional: N for Nth most recent)",
        category="system",
        args_schema={"n": "int?"},
    )(_trace_log)

    registry.register(
        "/training-plan",
        description="Show training data status and fine-tuning readiness",
        category="system",
    )(_training_plan)

    # Phase 23 — diagnostics + viewer cluster
    registry.register(
        "/capability-audit",
        description="Audit all registered capabilities for status and gaps",
        category="system",
    )(_capability_audit)

    registry.register(
        "/memory-curate",
        description="Review recent logs and propose durable memories for confirmation",
        category="system",
        intents=["memory_curate"],
    )(_memory_curate)

    registry.register(
        "/mcp-setup",
        description="Auto-configure MCP tool servers",
        category="system",
    )(_mcp_setup)

    registry.register(
        "/repair-adwi",
        description="Run full system repair: env check, deps, config drift",
        category="system",
    )(_repair_adwi)

    registry.register(
        "/run-safe",
        description="Run an action through the safety-gated executor",
        category="system",
        args_schema={"query": "str?"},
    )(_run_safe)

    registry.register(
        "/learn-from-last-error",
        description="Analyze the most recent error and propose a fix or memory",
        category="system",
        intents=["learn_from_error"],
    )(_learn_from_last_error)

    registry.register(
        "/secrets-status",
        description="Check which secrets files are present (never reveals values)",
        category="system",
    )(_secrets_status)

    registry.register(
        "/journal",
        description="Show last 60 lines of the Adwi journal",
        category="system",
    )(_journal)

    registry.register(
        "/mistakes",
        description="Show last 60 lines of the mistakes-and-fixes log",
        category="system",
    )(_mistakes)

    registry.register(
        "/nightly-log",
        description="Show recent nightly run log (optional: N for Nth most recent)",
        category="system",
        args_schema={"n": "int?"},
    )(_nightly_log)

    registry.register(
        "/inspect-code",
        description="Read and explain an Adwi source file",
        category="system",
        intents=["inspect_code"],
        args_schema={"path": "str"},
    )(_inspect_code)
