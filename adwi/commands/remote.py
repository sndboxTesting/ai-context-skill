"""
commands/remote.py — Remote access + Home Assistant status commands (Phase 18).

Phase 18 tranche (read-only/status subset):
  /remote-status  — Tailscale + cloudflared + HA connectivity status (read-only
                    subprocess + HTTP GET; aliases /remote and /tailscale)
  /ha             — Query HA API via HTTP GET (states, services, config, events,
                    history, logbook, or specific entity_id). Read-only.

Deferred (externally visible side effect):
  /notify         — HTTP POST to HA notification service (sends real push
                    notification to iPhone). Deferred because it produces an
                    externally visible action that cannot be un-sent. Migrate in
                    a later phase after dispatch_intent() slot-mapping is audited
                    and a test-safe guard (e.g., HA_TOKEN gate checked in test)
                    is confirmed sufficient.

All included commands are bounded to read-only network calls. No mutations.
No input() on any path (HA_TOKEN gate triggers early return before any prompt).
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


def _remote_status(args: str, ctx: dict) -> None:
    _cli().cmd_remote_status()


def _ha(args: str, ctx: dict) -> None:
    _cli().cmd_ha(args)


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/remote-status",
        aliases=["/remote", "/tailscale"],
        description="Show Tailscale, cloudflared, and Home Assistant connectivity (read-only status)",
        category="remote",
        intents=["remote_status"],
    )(_remote_status)

    registry.register(
        "/ha",
        description="Query Home Assistant API (states, services, config, entity_id — all GET, read-only)",
        category="remote",
        intents=["ha_query"],
        args_schema={"query": "str?"},
    )(_ha)
