# Local AI Stack Overview

**Last Updated:** 2026-06-15
**Maintained by:** Adwi nightly loop

---

## Architecture Summary

Suneel's local AI ecosystem ("Adwi") runs entirely on-device on an Apple M4 Max (64 GB unified RAM). No cloud dependency for inference — cloud is used only as an optional fallback via Open WebUI's Gemini route.

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
│   adwi CLI (adwi_cli.py)  ·  Open WebUI (:3000)            │
│   n8n workflows (:5678)   ·  local-command-api (:5055)      │
└────────────────────┬────────────────────────────────────────┘
                     │ dispatch_natural() / ask_adwi()
┌────────────────────▼────────────────────────────────────────┐
│                   INFERENCE LAYER                           │
│   Ollama (:11434)                                           │
│   ├─ adwi:latest      18.6 GB  Qwen3 MoE 30B  (reasoning)  │
│   ├─ qwen3:0.6b        0.5 GB  (instant NLU classification) │
│   ├─ minicpm-v:latest  5.5 GB  (local vision)              │
│   ├─ llama3.1:8b       4.9 GB  (general fallback)          │
│   └─ nomic-embed-text  0.3 GB  (embeddings)                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   MEMORY & KNOWLEDGE LAYER                  │
│   adwi/memory.db     SQLite ledger (AdwiMemory class)       │
│   adwi/knowledge.db  SQLite vector store (chunks + Q&A)     │
│   adwi/rag-db/       RAG notes index                        │
│   obsidian-vault/    Structured markdown knowledge base     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│               SUPPORTING SERVICES (Docker / Colima)         │
│   suneel-open-webui  :3000   Open WebUI frontend            │
│   suneel-n8n         :5678   Workflow automation            │
│   suneel-searxng     :8888   Private web search             │
│   suneel-qdrant      :6333   Vector database                │
│   obsidian-bridge    :5056   Vault HTTP API (local only)    │
│   private-gpt        :8001   RAG over private docs          │
└─────────────────────────────────────────────────────────────┘
```

## Key File Locations

| Purpose | Path |
|---|---|
| Main CLI | `adwi/adwi_cli.py` |
| Nightly loop | `adwi/nightly.py` |
| Overnight learner | `adwi/overnight_learn.py` |
| Memory ledger | `adwi/memory.db` |
| Knowledge vector DB | `adwi/knowledge.db` |
| Bin scripts | `bin/` (41 scripts) |
| Secrets | `secrets/secrets.local.env` |
| API tokens | `config/.env` |
| Obsidian vault | `obsidian-vault/` |
| System log | `logs/adwi_system_log.md` |
| Docker compose | `local-ai-stack/docker-compose.yml` |

## LaunchAgents (macOS Background Services)

| Label | Schedule | What It Does |
|---|---|---|
| `com.suneel.adwi-nightly` | 2:00 AM | Skill discovery, self-heal, evals, git backup |
| `com.suneel.adwi-git-backup` | periodic | Git push to GitHub |
| `com.suneel.openwebui-knowledge-watcher` | on login | Syncs .md files to Open WebUI Knowledge |
| `com.suneel.obsidian-bridge` | on login | Vault HTTP API on :5056 |
| `com.suneel.qdrant` | on login | Qdrant vector DB |
| `homebrew.mxcl.ollama` | on login | Ollama inference engine |

## Quick Commands

```bash
adwi                          # start interactive CLI
adwi /memory-recall <query>   # semantic search across memory + vault
adwi /web-search <query>      # private web search via SearXNG
adwi /obsidian-search <query> # search vault markdown files
adwi /status                  # full stack health check
adwi /self-heal               # run diagnostics and auto-fix
```
