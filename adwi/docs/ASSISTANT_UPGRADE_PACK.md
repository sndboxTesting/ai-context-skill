# Adwi — Assistant Upgrade Pack (Phase 5)

Added 2026-06-18. Upgrades Adwi from a command-dispatching REPL into a proactive,
browser-capable, research-capable personal assistant.

---

## Commands

| Slash command | NLU phrase examples | Description |
|---|---|---|
| `/research <question>` | "research X for me", "deep dive into X" | Multi-source research with citations; saves to `notes/research/` |
| `/research-save <question>` | "save research about X" | Same as `/research`, also appends to Obsidian daily note |
| `/browser-delegate <task>` | "use browser to X", "browser task: X" | Playwright agent; stops before any form-submit / login / payment |
| `/browser-delegate-dry-run <task>` | "browser agent dry run: X" | Describes what it would do without taking any action |
| `/daily-brief` | "give me my daily brief", "morning brief" | Service status + Gmail + AI priorities + learning tip; saves to `notes/daily-briefs/` |
| `/daily-brief --n8n` | (machine-only) | Same data as `/daily-brief` but emits a single JSON line; for n8n / Safe Command API use |
| `/tech-radar` | "tech radar", "scan new AI tools" | Scans 6 AI/dev areas and outputs try-now/watch/ignore recommendations |
| `/memory-curate` | "curate memories", "propose new memories" | Reviews recent logs, proposes durable memories, requires explicit Y/N per item |
| `/assistant-upgrade-status` | "upgrade pack status" | Shows all commands, optional API key status, output paths |

---

## Examples

```
> /research what are the best vector databases for local AI in 2025
> /research-save Ollama performance tuning techniques
> /browser-delegate go to n8n.io and find the latest blog post title
> /browser-delegate-dry-run check the Qdrant changelog on github.com
> /daily-brief
> /daily-brief --n8n
> /tech-radar
> /memory-curate
> /assistant-upgrade-status
```

---

## Optional environment variables

All keys live in `adwi/config/.env`. Add them to unlock higher-quality output.
None are required — every command degrades safely to local Ollama.

| Variable | Purpose | Without it |
|---|---|---|
| `EXA_API_KEY` | Exa neural search for `/research` | SearXNG-only results |
| `TAVILY_API_KEY` | Tavily web search for `/research` + `/daily-brief` | SearXNG-only results |
| `FIRECRAWL_API_KEY` | Full-page markdown extraction | Skips deep-fetch step |
| `OPENWEBUI_API_KEY` | Cloud LLM for synthesis and brief writing | Falls back to local `adwi:latest` |

See `adwi/config/.env.example` for the variable names (values are gitignored).

---

## Output locations

| Command | Notes output path | Obsidian |
|---|---|---|
| `/research` | `notes/research/YYYY-MM-DD-<slug>.md` | No |
| `/research-save` | `notes/research/YYYY-MM-DD-<slug>.md` | Yes — appended to daily note |
| `/browser-delegate` | `notes/browser-tasks/YYYY-MM-DD-<slug>.md` | No |
| `/daily-brief` | `notes/daily-briefs/YYYY-MM-DD.md` | Yes — appended to daily note |
| `/tech-radar` | `notes/tech-radar/YYYY-MM-DD.md` | No |
| `/memory-curate` | Confirmed items stored in `memory.db` | No |

---

## n8n daily brief integration

### Safe Command API route

The Safe Command API (`:5055`) has a dedicated allowlisted route:

```
GET http://127.0.0.1:5055/adwi-daily-brief-n8n
Header: X-Adwi-Secret: <your ADWI_LOCAL_SECRET>
```

Returns a JSON wrapper:

```json
{
  "route": "/adwi-daily-brief-n8n",
  "returncode": 0,
  "stdout": "{\"ok\":true,\"generated_at\":\"...\",\"mode\":\"n8n\",...}",
  "stderr": ""
}
```

Parse `response.body.stdout` as JSON after trimming whitespace.

### `/daily-brief --n8n` JSON schema

```json
{
  "ok": true,
  "generated_at": "2026-06-18T07:00:00.123456",
  "mode": "n8n",
  "services": {
    "ollama":    "up",
    "qdrant":    "up",
    "safe_api":  "up",
    "searxng":   "up",
    "open_webui": "down",
    "n8n":       "up"
  },
  "gmail": {
    "available": true,
    "unread_count": 3,
    "summary": "• sender@example.com: Subject line...",
    "warnings": []
  },
  "brief": "## Priorities\n1. ...\n\n## Inbox\n...",
  "saved_to": "/Users/MAC/SuneelWorkSpace/adwi/notes/daily-briefs/2026-06-18.md",
  "warnings": [],
  "errors": []
}
```

Service values are `"up"` or `"down"` (2-second HTTP timeout per service).
Gmail `available: false` means the token is missing or Gmail threw an error; the brief still runs.

### n8n workflow wiring (manual steps)

1. In n8n, add an **HTTP Request** node:
   - Method: `GET`
   - URL: `http://127.0.0.1:5055/adwi-daily-brief-n8n`
   - Headers: `X-Adwi-Secret` → `{{ $env.ADWI_LOCAL_SECRET }}`
2. Add a **Code** node after it:
   ```javascript
   const raw = $input.item.json.stdout.trim();
   return JSON.parse(raw);
   ```
3. Wire downstream nodes to `brief`, `gmail.summary`, `services`, etc.
4. Set trigger: **Schedule** → daily at 07:00 (or push to `/daily-brief-trigger` webhook).

> **Secret safety**: The `ADWI_LOCAL_SECRET` value is never printed or logged by the API. Only the route name, stdout, and stderr appear in n8n execution logs.

---

## Safety model

| Capability | Safety gate |
|---|---|
| `/research` | Read-only web search + local LLM. No writes except to approved `notes/` path. |
| `/browser-delegate` | Regex screens task for risky verbs (submit, sign up, login, purchase, delete). Stops and asks confirmation. Detects auth/paywall walls and halts. Dry-run mode takes no action at all. |
| `/daily-brief` | Gmail read-only. No emails sent. Obsidian write via Bridge. `notes/` write only. |
| `/memory-curate` | Every proposed memory requires explicit `Y` confirmation. `N` skips. Aborts cleanly on any error. |
| All commands | Respect `PathValidator` and `BLOCKED_PATHS`. No secrets, no `~/.ssh`, no `/etc`. |

---

## Known gaps

- `/research`: no follow-up question flow (one-shot only).
- `/browser-delegate`: form-filling and click actions not implemented (blocked by safety design; requires additional confirmation gates before enabling).
- `/daily-brief --n8n`: service probe uses a 2-second HTTP timeout — slow/hanging services may show `"down"` if they take >2s to respond. Increase `timeout` in `_svc_probe()` if needed.
- Safe Command API server (`:5055`) must be manually restarted to pick up the `/adwi-daily-brief-n8n` route: `adwi/bin/stop-command-api && adwi/bin/start-command-api`.

---

## Eval results (2026-06-18 CYCLE-7)

Full evals run with Ollama after all NLU fixes. **35 new upgrade_pack scenarios added** (26 P1 + 9 P2).

| Eval | Scenarios | Pass | Rate |
|------|-----------|------|------|
| P1 | 1,834 | 1,755 | 95.7% |
| P2 | 570 | 553 | 97.0% |
| **Combined (dedup)** | **~2,283** | **~2,187** | **~95.8%** |

Zero upgrade_pack intent routing failures after fixes (memory_curate regex, rag_search word-boundary, save-research regex). Remaining failures are pre-existing LLM variance in chat/status/git_status families.

---

## Next recommended improvements

1. **Restart Safe Command API server** to activate `/adwi-daily-brief-n8n` route: `adwi/bin/stop-command-api && adwi/bin/start-command-api`.
2. **Wire n8n "Adwi — Brief" workflow** (`adwi/automation/workflows/adwi-daily-brief.json`) — import into n8n, activate, add downstream Telegram/Slack notification node.
3. **Add `/daily-brief --n8n` flag to adwi-nightly** so the 2 AM LaunchAgent saves a JSON snapshot for historical review.
4. **Implement `/research` follow-up**: after first brief, prompt "Dig deeper into: [topic]?" using the saved research context.
5. **Add eval cases for LLM-only paths**: "what's on my plate today" and "scan trending AI this week" are LLM-routed (no regex hit) — add to a targeted adversarial eval.
