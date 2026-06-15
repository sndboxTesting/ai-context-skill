# Adwi System Log
<!-- Append-only. Every change, success, failure, and pending task recorded here. -->

---

## 2026-06-15 — Phase 1: Environment Discovery & Baseline Audit

**Status: COMPLETE**

### Findings
- Hardware: Apple M4 Max, 64 GB RAM, 712 GB free disk
- Ollama models loaded: adwi:latest (18.6GB), nomic-embed-text, qwen3:0.6b, llama3.1:8b, minicpm-v:latest
- Docker containers: suneel-open-webui (:3000), suneel-n8n (:5678), suneel-searxng (:8888), suneel-qdrant (:6333)
- Active services: local-command-api (:5055), private-gpt (:8001)
- LaunchAgents: adwi-nightly (2AM), adwi-git-backup, openwebui-knowledge-watcher, qdrant, ollama
- knowledge.db: tables `chunks` + `qa_pairs` with embedding columns — operational, 2065 records post overnight run
- memory.db: ledger via AdwiMemory class in adwi/memory.py
- NLU dispatch: adwi_cli.py:3354 `dispatch_natural()`, :641 `ask_adwi()`, :3170 `cmd_memory_recall()`
- SearXNG NOTE: running on host port **8888** (container maps 8080→8888)

### Gaps Identified
- No obsidian-vault/ directory
- No Obsidian MCP server or vault HTTP bridge
- /memory-recall only queries memory.db — does not traverse vault .md files
- No /web-search command wired to SearXNG
- nightly.py lacks: system health checks, web research, Obsidian daily note output, "Pending Approval" section
- No config/.env for API tokens

---

## 2026-06-15 — Phase 2: Vault & Directory Provisioning

**Status: COMPLETE**

### Actions Taken
- Created obsidian-vault/ with subdirs: inbox/ projects/ knowledge/ automations/ prompts/ logs/ daily-notes/ mcp-config/ .obsidian/
- Created config/ for .env API token storage
- Created logs/ for this system log
- Wrote starter notes: Local AI Stack Overview, Agent Rules & Guardrails, Troubleshooting Log
- Wrote config/.env with placeholder tokens (Brave Search, Tavily)
- Wrote .gitignore entries for config/.env and vault runtime files

---

## 2026-06-15 — Phase 3: Dual-Layer MCP Integration

**Status: COMPLETE**

### Actions Taken
- Wrote mcp-servers/obsidian-bridge/server.py — lightweight HTTP server exposing vault read/write/search/append on :5056
- Wrote mcp-servers/obsidian-bridge/start.sh and stop.sh
- Added com.suneel.obsidian-bridge.plist LaunchAgent (starts with login, port 5056)
- Confirmed Playwright MCP available via npx @playwright/mcp
- Extended adwi_cli.py: OBSIDIAN_VAULT path constant + cmd_obsidian_read/write/search + dispatch intents

---

## 2026-06-15 — Phase 4: Web Search & /memory-recall Dual-Layer

**Status: COMPLETE**

### Actions Taken
- Added searxng_search() helper to adwi_cli.py targeting :8888
- Added /web-search command + "web_search" NLU intent in dispatch_natural()
- Extended cmd_memory_recall() to traverse both memory.db AND obsidian-vault/**/*.md
- Added config/.env loader at adwi_cli.py startup (non-fatal if absent)
- Added Brave/Tavily fallback stubs guarded by env var presence

---

## 2026-06-15 — Phase 5: Nightly Maintenance Script Extension

**Status: COMPLETE**

### Actions Taken
- Extended nightly.py with step_system_health(): brew outdated, npm outdated, docker stats, disk check
- Extended nightly.py with step_web_research(): queries SearXNG for release notes on stack tools
- Extended nightly.py with step_obsidian_daily_note(): writes daily note to obsidian-vault/daily-notes/
- Extended step_write_report() to produce full morning_brief.md with "Pending User Approval" section
- LaunchAgent com.suneel.adwi-nightly already in place at 2:00 AM — no plist change needed

---

## 2026-06-15 — Phase 6: Known-Good State Documentation

**Status: COMPLETE**

### Actions Taken
- Wrote obsidian-vault/knowledge/rollback-and-recovery.md with full rollback instructions

---

## Pending / Watch Items
- [ ] Populate config/.env with real Brave Search / Tavily API keys when ready
- [ ] Point Obsidian desktop app at ~/SuneelWorkSpace/obsidian-vault to open the vault
- [ ] Load com.suneel.obsidian-bridge LaunchAgent: `launchctl load ~/Library/LaunchAgents/com.suneel.obsidian-bridge.plist`
- [ ] Run `/web-search ollama release notes` from adwi to verify SearXNG wiring
- [ ] Run `/obsidian-search local AI` to verify vault bridge
