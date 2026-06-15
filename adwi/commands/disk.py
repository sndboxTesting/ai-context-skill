"""
commands/disk.py — Filesystem & disk analysis commands.

Wraps existing adwi_cli.py implementations via lazy import to avoid circular
dependencies. As functions are migrated out of adwi_cli.py they can be moved
here and the lazy import removed.
"""

from __future__ import annotations

import importlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from adwi.command_registry import CommandRegistry


def _cli():
    """Lazy import of adwi_cli to avoid circular dependency at registry init time."""
    import importlib.util
    import sys
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


def _disk(args: str, ctx: dict) -> None:
    _cli().cmd_disk_usage(args or None)


def _large_files(args: str, ctx: dict) -> None:
    parts = args.split()
    path  = parts[0] if parts else None
    size_mb = 200
    if len(parts) > 1:
        m = re.match(r"(\d+)", parts[1])
        size_mb = int(m.group(1)) if m else 200
    _cli().cmd_large_files(path, min_mb=size_mb)


def _old_files(args: str, ctx: dict) -> None:
    parts = args.split()
    path  = parts[0] if parts else None
    days  = 365
    if len(parts) > 1:
        m = re.match(r"(\d+)", parts[1])
        if m:
            unit = parts[1].rstrip("0123456789").lower()
            n    = int(m.group(1))
            days = n * (365 if "year" in unit else 30 if "month" in unit else 1)
    _cli().cmd_old_files(path, days=days)


def _duplicates(args: str, ctx: dict) -> None:
    _cli().cmd_find_duplicates(args or None)


def _organize(args: str, ctx: dict) -> None:
    _cli().cmd_organize_suggest(args or None)


def _cleanup(args: str, ctx: dict) -> None:
    _cli().cmd_cleanup_suggest(args or None)


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/disk",
        description="Disk usage summary for home / target path",
        aliases=["/disk-usage"],
        category="filesystem",
        intents=["disk_usage"],
        args_schema={"path": "str?"},
    )(_disk)

    registry.register(
        "/large-files",
        description="Find files larger than N MB (default 200)",
        category="filesystem",
        intents=["large_files"],
        args_schema={"path": "str?", "size_mb": "int?"},
    )(_large_files)

    registry.register(
        "/old-files",
        description="Find files not touched in N days (default 365)",
        category="filesystem",
        intents=["old_files"],
        args_schema={"path": "str?", "days": "int?"},
    )(_old_files)

    registry.register(
        "/find-duplicates",
        description="Find duplicate files (hash comparison)",
        aliases=["/duplicates"],
        category="filesystem",
        intents=["duplicates"],
        args_schema={"path": "str?"},
    )(_duplicates)

    registry.register(
        "/organize-suggest",
        description="Suggest folder reorganization for a directory",
        aliases=["/organize"],
        category="filesystem",
        intents=["organize"],
        args_schema={"path": "str?"},
    )(_organize)

    registry.register(
        "/cleanup-suggest",
        description="Suggest files safe to delete",
        aliases=["/cleanup"],
        category="filesystem",
        intents=["cleanup"],
        args_schema={"path": "str?"},
    )(_cleanup)
