---
type: map-of-content
status: active
tags: [system, architecture, infrastructure]
updated: 2026-06-21
---

# System Map

Complete map of every service, port, and data flow in the Adwi workspace.

## Process Topology

```
iPhone / Telegram / Browser
     │
     ├── Cloudflare Tunnel (:443) ──► n8n :5678
     │                                    │
     ├── Tailscale VPN ──────────── Home Assistant :8123
     │                                    │
     └── Telegram long-poll ────── telegram-bridge/bot.py ──┐
                                                             │
                                         ┌───────────────────▼──────┐
                                         │  Safe Command API :5055   │
                                         │  26 allowlisted routes    │
                                         │  X-Adwi-Secret required   │
                                         └───────────┬───────────────┘
                                                     │
                                         adwi_cli.py (REPL)
                                                     │
              ┌──────────────────────────────────────┤
              │              │            │           │
         Ollama :11434   Qdrant :6333  SearXNG :8888 memory.db
              │              │
        adwi:latest    nomic-embed     Obsidian Bridge :5056
        llama3.1:8b    nlu_fixtures    obsidian-vault/
        qwen3:0.6b     knowledge.db
        minicpm-v
```

## Port Reference

| Port | Service | Layer | Notes |
|------|---------|-------|-------|
| :5055 | Safe Command API | Host | 26 routes + 1 E2E Popen; auth required |
| :5056 | Obsidian Bridge | Host (LaunchAgent) | Vault CRUD; no auth yet |
| :5678 | n8n | Docker | Workflow automation |
| :3000 | Open WebUI | Docker | Browser chat |
| :6333 | Qdrant | Docker (LaunchAgent) | Vector DB |
| :8888 | SearXNG | Docker | Private search |
| :11434 | Ollama | Host (brew) | LLM inference |
| :6006 | Arize Phoenix | Host (LaunchAgent) | OTel observability |
| :4000 | Grafana | Docker | Dashboards |
| :9090 | Prometheus | Docker | Metrics |
| :3100 | Loki | Docker | Log aggregation |
| :8123 | Home Assistant | Docker | iPhone control |

## LaunchAgents

| Agent | Schedule |
|-------|---------|
| `adwi-git-backup` | every 30 min |
| `adwi-nightly` | 2:00 AM |
| `adwi-scheduled-send` | every 2 min |
| `obsidian-bridge` | KeepAlive |
| `openwebui-knowledge-watcher` | KeepAlive |
| `phoenix` | KeepAlive |
| `caffeinate` | KeepAlive |
| `qdrant` | on demand |
| `telegram-bridge` | KeepAlive (optional) |

## Hard-Blocked Paths (PathValidator)

```
~/.ssh/              ~/.aws/             ~/.gnupg/
~/.kube/             ~/Library/Keychains/ ~/Library/Passwords/
~/SuneelWorkSpace/secrets/   /etc/   /private/   /System/
```

## Related Notes

- [[knowledge/Automation Map]]
- [[knowledge/Memory and Knowledge Map]]
- [[projects/Adwi]]
- [README §2 Infrastructure](../../README.md)

## Next Improvements

- [ ] Add Obsidian Bridge auth (same X-Adwi-Secret header pattern)
- [ ] Bind Docker host ports to 127.0.0.1 to remove LAN exposure
- [ ] Harden Grafana password
- [ ] Disable Open WebUI signup
