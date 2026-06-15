#!/usr/bin/env python3
"""
adwi/voice.py — Local Voice I/O Pipeline (Pillar C)

STT: faster-whisper (CoreML / Apple Silicon optimized)
TTS: piper-tts (neural TTS, Metal-accelerated via espeak-ng)

Both run entirely locally — no cloud, no API key required.
Models are auto-downloaded to ~/.adwi-voice/ on first use.
"""

import os
import sys
import subprocess
import tempfile
import threading
from pathlib import Path

VOICE_DIR   = Path.home() / ".adwi-voice"
PIPER_MODEL = VOICE_DIR / "en_US-lessac-medium.onnx"
PIPER_CFG   = VOICE_DIR / "en_US-lessac-medium.onnx.json"

PIPER_MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
PIPER_CFG_URL   = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

WHISPER_MODEL = "base.en"   # fast English-only; upgrade to "small.en" for accuracy


# ── Lazy imports (packages live in adwi/.venv) ──────────────────────────────

def _import_whisper():
    try:
        from faster_whisper import WhisperModel
        return WhisperModel
    except ImportError:
        print("  faster-whisper not available — run: uv pip install faster-whisper", file=sys.stderr)
        return None


def _import_piper():
    try:
        from piper import PiperVoice
        return PiperVoice
    except ImportError:
        print("  piper-tts not available — run: uv pip install piper-tts", file=sys.stderr)
        return None


# ── Model bootstrap ──────────────────────────────────────────────────────────

def _ensure_piper_model() -> bool:
    if PIPER_MODEL.exists() and PIPER_CFG.exists():
        return True
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    import urllib.request
    print("  [voice] Downloading piper voice model (~63 MB) …")
    for url, dst in [(PIPER_MODEL_URL, PIPER_MODEL), (PIPER_CFG_URL, PIPER_CFG)]:
        try:
            urllib.request.urlretrieve(url, dst)
        except Exception as e:
            print(f"  [voice] Download failed: {e}")
            return False
    print("  [voice] Piper model ready.")
    return True


# ── STT — Speech To Text ─────────────────────────────────────────────────────

_whisper_model = None
_whisper_lock  = threading.Lock()


def transcribe(audio_path: str | Path, language: str = "en") -> str:
    """
    Transcribe an audio file to text using faster-whisper.
    Supports wav, mp3, m4a, ogg. Returns plain text string.
    """
    WhisperModel = _import_whisper()
    if WhisperModel is None:
        return ""

    global _whisper_model
    with _whisper_lock:
        if _whisper_model is None:
            print(f"  [voice] Loading Whisper model '{WHISPER_MODEL}' (first use — one-time download) …")
            _whisper_model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",          # Apple Silicon: cpu uses ANE via Metal internally
                compute_type="int8",   # fastest on ARM
            )

    segments, info = _whisper_model.transcribe(str(audio_path), language=language, beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip()


def record_mic(seconds: int = 6, sample_rate: int = 16000) -> Path | None:
    """
    Record from default microphone for `seconds` seconds.
    Uses sox if available, falls back to ffmpeg (both work on macOS).
    Returns path to .wav file or None on failure.
    """
    out = Path(tempfile.mktemp(suffix=".wav"))
    print(f"  [voice] Recording {seconds}s … speak now")

    sox_bin  = subprocess.run(["which", "sox"],    capture_output=True, text=True).stdout.strip()
    ffmpeg   = subprocess.run(["which", "ffmpeg"], capture_output=True, text=True).stdout.strip()

    if sox_bin:
        r = subprocess.run(
            [sox_bin, "-d", "-r", str(sample_rate), "-c", "1", "-b", "16", str(out),
             "trim", "0", str(seconds)],
            capture_output=True, text=True,
        )
    elif ffmpeg:
        r = subprocess.run(
            [ffmpeg, "-f", "avfoundation", "-i", ":0", "-t", str(seconds),
             "-ar", str(sample_rate), "-ac", "1", str(out), "-y"],
            capture_output=True, text=True,
        )
    else:
        print("  [voice] No recorder found — install: brew install sox")
        return None

    if r.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
        print(f"  [voice] Recording failed: {(r.stderr or r.stdout)[:200].strip()}")
        return None
    return out


# ── TTS — Text To Speech ─────────────────────────────────────────────────────

_piper_voice = None
_piper_lock  = threading.Lock()


def speak(text: str, play: bool = True) -> Path | None:
    """
    Synthesize text to speech using piper-tts (local, neural, Apple Metal).
    Returns path to .wav file. If play=True, plays immediately via afplay.
    """
    PiperVoice = _import_piper()
    if PiperVoice is None:
        return None
    if not _ensure_piper_model():
        return None

    global _piper_voice
    with _piper_lock:
        if _piper_voice is None:
            print("  [voice] Loading piper voice model …")
            _piper_voice = PiperVoice.load(str(PIPER_MODEL))

    out = Path(tempfile.mktemp(suffix=".wav"))
    with open(out, "wb") as f:
        _piper_voice.synthesize(text, f)

    if play:
        subprocess.run(["afplay", str(out)], check=False)

    return out


# ── CLI helpers for adwi_cli.py ──────────────────────────────────────────────

def cmd_voice_in_impl() -> str:
    """
    Record 6 seconds of mic input, transcribe, and return text.
    Prints status messages; returns transcription or empty string.
    """
    audio = record_mic(seconds=6)
    if audio is None:
        return ""
    print("  [voice] Transcribing …")
    text = transcribe(audio)
    try:
        audio.unlink()
    except Exception:
        pass
    if text:
        print(f"  [voice] Heard: {text}")
    return text


def cmd_voice_out_impl(text: str) -> None:
    """Synthesize and play text via piper-tts."""
    if not text.strip():
        return
    speak(text, play=True)
