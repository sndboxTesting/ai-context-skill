---
type: project
status: active
tags: [adwi, ai-os, local-ai]
updated: 2026-06-21
---

# Adwi — Project Overview

Adwi is a local AI operating system running on Apple M4 Max (64 GB). It is a personal AI assistant, not a library — it runs as a terminal REPL and a set of daemon services. All inference is local; cloud is an optional fallback only.

## Core Stats

| Metric | Value |
|--------|-------|
| Commands | 184 registered |
| NLU intents | 115 classes |
| NLU accuracy | 98.3% combined (P1: 98.4%, P2: 98.2%) |
| Eval scenarios | 2,283 (P1 + P2 deduped) |
| Safety breaches | 0 |
| Regex fast-path | 67.8% of queries |
| Test suite | 481 NLU + 320 registry + 80 Telegram + more |

## Entry Points

| What | How |
|------|-----|
| Interactive REPL | `bin/adwi` |
| Telegram remote | `python3 adwi/services/telegram-bridge/bot.py` |
| Safe Command API | `bin/start-command-api` (`:5055`) |
| n8n automation | Docker `:5678` |
| Nightly loop | LaunchAgent → `adwi/nightly.py` (2 AM) |

## Key Source Files

| File | What it owns |
|------|-------------|
| `adwi/adwi_cli.py` | REPL, 184 commands, NLU pipeline |
| `adwi/reason_engine.py` | LangGraph Planner→Executor→Critic |
| `adwi/memory.py` | SQLite memory + Qdrant NLU fixtures |
| `adwi/path_validator.py` | Deny-first path safety gate |
| `adwi/nightly.py` | 10-step 2 AM maintenance loop |
| `adwi/gmail_helper.py` | Gmail OAuth2 integration (864 lines) |
| `adwi/services/command-api/server.py` | Safe API (26 routes) |
| `adwi/services/telegram-bridge/bot.py` | Telegram bridge (9 commands) |

## Phases Completed

- **Phase 1–10**: Infrastructure, LangGraph, memory, security, SimLab eval harness
- **Phase 11–23**: CommandRegistry migration (Gmail clusters, diagnostics, remote/HA)
- **Phase 5 (Upgrade Pack)**: Research, browser delegate, daily brief, tech radar, memory curator
- **Waves 1–8 (2026-06-21)**: Telegram bridge, 6 observability bin scripts, codex-advisor skill

## Related Notes

- [[knowledge/System Map]]
- [[knowledge/Automation Map]]
- [[knowledge/Eval and Reliability Map]]
- [[knowledge/Memory and Knowledge Map]]
- [[knowledge/Ideas Index]]
- [Full README](../../README.md)
- [CLAUDE.md session orientation](../../CLAUDE.md)

## Next Improvements

- [ ] Resolve 1 open NHR item in `adwi/docs/NLU_REPAIR_BACKLOG.md`
- [ ] Obsidian bridge auth (same X-Adwi-Secret pattern as Safe API)
- [ ] Harden Docker LAN exposure (bind host ports to 127.0.0.1)
- [ ] Voice input via whisper.cpp → [[projects/ideas/Voice Input]]
- [ ] Multi-agent parallel execution → [[projects/ideas/Multi-Agent Execution]]
