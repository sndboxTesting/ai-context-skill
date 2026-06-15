"""
commands/knowledge.py — Memory, RAG, web search, and Obsidian commands.
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


def _memory_recall(args: str, ctx: dict) -> None:
    _cli().cmd_memory_recall(args)


def _memory_scan(args: str, ctx: dict) -> None:
    _cli().cmd_memory_scan()


def _memory_stats(args: str, ctx: dict) -> None:
    _cli().cmd_memory_stats()


def _memory_context(args: str, ctx: dict) -> None:
    _cli().cmd_memory_context(args)


def _rag_search(args: str, ctx: dict) -> None:
    _cli().cmd_rag_search(args)


def _web_search(args: str, ctx: dict) -> None:
    _cli().cmd_web_search(args)


def _exa_search(args: str, ctx: dict) -> None:
    _cli().cmd_exa_search(args)


def _tavily_search(args: str, ctx: dict) -> None:
    _cli().cmd_tavily_search(args)


def _obsidian_search(args: str, ctx: dict) -> None:
    _cli().cmd_obsidian_search(args)


def _obsidian_read(args: str, ctx: dict) -> None:
    _cli().cmd_obsidian_read(args)


def _obsidian_write(args: str, ctx: dict) -> None:
    _cli().cmd_obsidian_write(args)


def _obsidian_daily(args: str, ctx: dict) -> None:
    _cli().cmd_obsidian_daily()


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/memory-recall",
        description="Semantic search over personal memory ledger",
        aliases=["/recall"],
        category="knowledge",
        intents=["memory_recall"],
        args_schema={"query": "str"},
    )(_memory_recall)

    registry.register(
        "/memory-scan",
        description="Index terminal history and git commits into memory",
        aliases=["/scan"],
        category="knowledge",
        intents=["memory_scan"],
    )(_memory_scan)

    registry.register(
        "/memory-stats",
        description="Show memory ledger statistics",
        category="knowledge",
        intents=["memory_stats"],
    )(_memory_stats)

    registry.register(
        "/memory-context",
        description="Retrieve context block for a query",
        category="knowledge",
        intents=["memory_context"],
        args_schema={"query": "str"},
    )(_memory_context)

    registry.register(
        "/rag",
        description="RAG semantic search over workspace notes",
        aliases=["/rag-search"],
        category="knowledge",
        intents=["rag_search"],
        args_schema={"query": "str"},
    )(_rag_search)

    registry.register(
        "/web",
        description="Search the web via SearXNG",
        aliases=["/web-search", "/search"],
        category="knowledge",
        intents=["web_search"],
        args_schema={"query": "str"},
    )(_web_search)

    registry.register(
        "/exa",
        description="Neural web search via Exa",
        aliases=["/exa-search"],
        category="knowledge",
        intents=["exa_search"],
        args_schema={"query": "str"},
    )(_exa_search)

    registry.register(
        "/tavily",
        description="Tavily AI web search",
        aliases=["/tavily-search"],
        category="knowledge",
        intents=["tavily_search"],
        args_schema={"query": "str"},
    )(_tavily_search)

    registry.register(
        "/obsidian-search",
        description="Search Obsidian vault",
        aliases=["/vault-search"],
        category="knowledge",
        intents=["obsidian_search"],
        args_schema={"query": "str"},
    )(_obsidian_search)

    registry.register(
        "/obsidian-read",
        description="Read an Obsidian note by title",
        category="knowledge",
        intents=["obsidian_read"],
        args_schema={"path": "str"},
    )(_obsidian_read)

    registry.register(
        "/obsidian-write",
        description="Create or update an Obsidian note",
        category="knowledge",
        intents=["obsidian_write"],
        args_schema={"path": "str"},
    )(_obsidian_write)

    registry.register(
        "/obsidian-daily",
        description="Open today's daily note in Obsidian",
        aliases=["/daily-note"],
        category="knowledge",
        intents=["obsidian_daily"],
    )(_obsidian_daily)
