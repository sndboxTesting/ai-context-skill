# Adwi Capability Roadmap

Tracks what has been built, what is planned, and ideas under evaluation.
Use `/add-capability-plan <idea>` to add new ideas. Use `/daily-improve` to review and update.

---

## Completed

- [x] Ollama local model runner with adwi:latest (Qwen3 MoE 30.5B, 131K context)
- [x] Open WebUI browser chat at http://localhost:3000
- [x] n8n automation engine at http://localhost:5678
- [x] SearXNG local web search at http://localhost:8888
- [x] Safe Command API at http://127.0.0.1:5055
- [x] Open WebUI Knowledge auto-sync watcher
- [x] Multiline terminal input (prompt_toolkit, Alt+Enter to send)
- [x] Streaming local responses (tokens appear as generated)
- [x] Capability registry (`adwi/capabilities.json`)
- [x] Learning journal + mistakes tracker
- [x] Image analysis via Gemini vision (`/image`, `/screenshot-analyze`)
- [x] YouTube auto-detection and summarization menu
- [x] Daily improvement routine (`/daily-improve`)
- [x] Cloud reasoning commands (`/reason`, `/review-plan`)
- [x] What-next advisor (`/what-next`)
- [x] Natural language routing (YouTube URLs, image paths, "what's next")
- [x] Full Mac filesystem read access (`/Users/MAC` expanded, hard-blocked: .ssh, secrets, keychains)
- [x] AI intent classifier: 3-layer (regex → qwen3:0.6b model → fallback), 11/11 test pass
- [x] Disk analysis: `/disk`, `/large-files`, `/old-files`, `/duplicates`, `/organize`, `/cleanup`
- [x] Local vision model: `minicpm-v` (5.5GB) — no cloud needed for images
- [x] Fast NLU model: `qwen3:0.6b` (522MB) — stays hot in memory alongside adwi
- [x] OLLAMA_MAX_LOADED_MODELS=3 + KEEP_ALIVE=30m — all models warm simultaneously
- [x] Zero-command natural language: just talk, Adwi figures out what to do automatically

---

## Phase 2 — Completed (2026-06-14)

- [x] RAG over notes — `/rag <query>` semantic search using nomic-embed-text, 64 docs indexed
- [x] Browser automation — `/browse <url>` with Playwright (JS-capable) + urllib fallback
- [x] Code execution sandbox — `/run-python` + `/run-bash` with confirm step + 30s timeout
- [x] Git + repo management — `/git status|log|diff|review|repos` for all workspace repos
- [x] Local image generation — `/generate-image <prompt>` via LocalAI (run `/mcp-setup` first)
- [x] Benchmark tool — `/benchmark` tests NLU speed, embed speed, main model tok/s
- [x] MCP tool servers — configured filesystem + fetch + memory servers (~/.config/mcp/servers.json)
- [x] Open WebUI tools bridge — adwi/open-webui-tools.py with 5 tool classes
- [x] n8n new routes — /rag-index, /git-status-workspace, /benchmark-adwi added to command API
- [x] 6 new NLU intents — rag_search, browse, git_status, generate_image, run_code, benchmark
- [x] adwi_cli.py — 495 lines added (1189→1684), 11 new regex patterns, all commands wired
- [x] Gmail integration — OAuth2 read-only, INBOX scoped, internalDate sorted, 50K emails

## Phase 3 — Completed (2026-06-14)

- [x] 10 MCP servers connected — Playwright, Fetch, GitHub, SQLite, Memory, Sequential Thinking, Qdrant, ComfyUI bridge, Adwi sandbox, Filesystem
- [x] Qdrant vector DB — Docker container running :6333, LaunchAgent for auto-start, collection: adwi-knowledge
- [x] Adwi sandbox MCP — 8 tools: run_python, run_bash, search_notes, git_status, read_file, list_files, adwi_status, note_append
- [x] ComfyUI MCP bridge — 3 tools: generate_image, comfyui_status, list_models (needs ComfyUI install separately)
- [x] SQLite workspace DB — notes, tasks, learnings tables at mcp-servers/workspace.db
- [x] GitHub MCP — suneeluhcl token saved, repos/issues/PRs accessible
- [x] /mcp command — shows all 10 servers with live-service check, colored status dots
- [x] bin/mcp-status script — terminal status overview, auto-starts Qdrant if offline
- [x] Claude Code settings — all 10 MCP servers also configured in ~/.claude/settings.json

## Phase 5 — Assistant Upgrade Pack (2026-06-18)

- [x] **Research Operator** — `/research <question>` + `/research-save` — deep multi-source research (SearXNG + optional Exa/Tavily/Firecrawl), produces cited brief saved to `notes/research/`
- [x] **Browser Delegate** — `/browser-delegate <task>` + dry-run mode — Playwright agent with confirmation gate before any form-submit/payment/auth action, saves to `notes/browser-tasks/`
- [x] **Daily Brief** — `/daily-brief` — proactive assistant brief: service status + Gmail snapshot + priorities + learning tip + setup suggestion, saves to `notes/daily-briefs/` + Obsidian daily note, n8n-callable
- [x] **Tech Radar** — `/tech-radar` — scans 6 AI/dev tech areas (OpenAI Agents, MCP, Ollama, browser agents, LangGraph, local voice/vision/RAG), categorises try-now/watch/ignore, saves to `notes/tech-radar/`
- [x] **Memory Curator** — `/memory-curate` — reviews recent logs, proposes 3-5 durable memories, requires explicit Y/N per item, never auto-stores
- [x] **Upgrade Status** — `/assistant-upgrade-status` — shows all 5 commands + optional API key status + output paths
- [x] 6 new NLU intents + regex patterns wired into `_ALL_INTENTS` and `_REGEX_INTENTS`
- [x] 68 total capability entries in `capabilities.json` (up from 62)

Optional env keys to unlock full power: `EXA_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `OPENWEBUI_API_KEY` (all in `adwi/config/.env.example`).

Next steps for Codex: wire `/daily-brief` into the n8n "Adwi — Brief" workflow, add eval test cases to `run_large_eval.py`/`run_large_eval_p2.py` for the 6 new intents, implement `/daily-brief --n8n` flag for machine-readable JSON output.

## Phase 4 — Planned

- [ ] Implement-from-video flow: paste video → "implement this" → plan → apply
- [ ] Article/URL implementation flow: paste article → extract ideas → build plan
- [ ] Conversation memory: persist multi-turn chat history between sessions
- [ ] Mistake pattern detection: auto-analyze mistakes-and-fixes.md and update prompts
- [ ] Scheduled self-improvement: n8n runs /daily-improve every morning
- [ ] LocalAI image model setup: run adwi-start-localai + wait for SD model download (~4GB)
- [ ] ComfyUI install: git clone + model download (~4GB), then bridge activates automatically
- [ ] Voice input: whisper.cpp for speech-to-text → adwi prompt
- [ ] Multi-agent: adwi spawns sub-agents for parallel research + implementation

---

## Phase 3 — Future Ideas

- [ ] Fine-tuning pipeline: collect good adwi outputs, fine-tune a small local model
- [ ] Voice input: whisper.cpp for local speech-to-text → adwi prompt
- [ ] Screen monitoring: periodic screenshot analysis to track what Suneel is working on
- [ ] Multi-agent: adwi spawns sub-agents for research + implementation in parallel
- [ ] Local code execution sandbox for safe AI-generated scripts
- [ ] Deepseek-R1 or similar local reasoning model when hardware allows

---

## Ideas Under Evaluation

_Nothing here yet. Use `/add-capability-plan <idea>` to add._

---
