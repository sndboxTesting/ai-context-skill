# Adwi Learning Journal

This journal tracks what Adwi has learned, what improved, and what patterns worked well.
Updated automatically by `/daily-improve` and synced to Open WebUI Knowledge.

---

## 2026-06-14 — Phase 1 Initialization

**What improved:**
- Context window upgraded from 2,048 → 131,072 tokens (Qwen3 MoE 30.5B)
- Multiline terminal input added via prompt_toolkit (Enter=newline, Alt+Enter=send)
- Streaming responses added for local model mode
- Capability registry created at `adwi/capabilities.json`
- Learning journal, mistakes tracker, and capability roadmap initialized
- Image analysis via Gemini vision added (`/image`, `/screenshot-analyze`)
- YouTube auto-detection: paste a YouTube URL → menu appears automatically
- Daily improvement routine added (`/daily-improve`)
- Cloud reasoning commands added (`/reason`, `/review-plan`)
- Natural language routing improved (YouTube URLs, image paths, "what's next")
- Summarize scripts upgraded from llama3.1:8b → adwi:latest

**What works well:**
- M4 Max + 64GB RAM handles 131K context without memory pressure
- Flash Attention + q8_0 KV cache keep memory efficient
- Open WebUI + Gemini covers vision and complex reasoning locally
- Knowledge watcher auto-syncs files dropped in open-webui-knowledge-upload/

**Rule learned:**
Always set `num_ctx` explicitly in Modelfile — Ollama defaults to 2048 which silently cripples long-context models.

---

## 2026-06-14 19:47

Smoke test entry — Phase 1 verification pass

---
