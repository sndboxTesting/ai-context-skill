"""
commands/voice.py — Voice I/O cluster (Phase 17).

Phase 17 (voice I/O cluster): voice-in, voice-out, voice-brief.

All three commands are local-device only — no network calls, no external
state mutation. Side effects are bounded to microphone recording and local
audio playback via piper-tts + afplay.

voice-in  : records mic, transcribes with faster-whisper, and re-dispatches
            the recognized text through the NLU pipeline (dispatch_natural).
            Aliases /voice and /listen preserved.

voice-out : synthesizes text to speech via piper-tts and plays via afplay.
            If no text arg is supplied, falls back to input() — preserved via
            _cli() delegation. No network; no file writes.

voice-brief: reads ~/Desktop/morning_brief.md, strips markdown formatting,
             and delegates to cmd_voice_out() (internal call stays within
             adwi_cli.py via _cli()). Capped at 3000 chars to avoid long
             sessions.
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


def _voice_in(args: str, ctx: dict) -> None:
    _cli().cmd_voice_in()


def _voice_out(args: str, ctx: dict) -> None:
    _cli().cmd_voice_out(args)


def _voice_brief(args: str, ctx: dict) -> None:
    _cli().cmd_voice_brief()


# ── Registration ──────────────────────────────────────────────────────────────


def register(registry: "CommandRegistry") -> None:
    registry.register(
        "/voice-in",
        aliases=["/voice", "/listen"],
        description="Record mic, transcribe with faster-whisper, dispatch as natural language",
        category="voice",
        intents=["voice_in"],
    )(_voice_in)

    registry.register(
        "/voice-out",
        description="Synthesize text to speech via piper-tts and play via afplay (local only)",
        category="voice",
        intents=["voice_out"],
        args_schema={"text": "str?"},
    )(_voice_out)

    registry.register(
        "/voice-brief",
        description="Read ~/Desktop/morning_brief.md aloud via piper-tts (local file + audio)",
        category="voice",
        intents=["voice_brief"],
    )(_voice_brief)
