# Adwi — Strict External-Model Priming File

> **PURPOSE:** Optimized for cold-start ingestion by Claude, Gemini, Copilot, GPT-4, or any LLM
> reading this for the first time. Minimal ambiguity. Current-state only. No historical narrative.
>
> **LAST VERIFIED:** 2026-06-17 against live code, config, and Qdrant.
>
> **GROUND TRUTH PRECEDENCE:** code > config > generator output > this file > README prose

---

## IDENTITY

| Property | Value |
|----------|-------|
| System | Adwi — local AI operating system |
| Operator | Suneel Bikkasani |
| Hardware | Apple M4 Max · 64 GB unified RAM · macOS 15 (Darwin 25.x) |
| Repo root | `~/SuneelWorkSpace/` |
| Entry point | `bin/adwi` → `python3 adwi/adwi_cli.py` |
| Primary model | `adwi:latest` (qwen3:30b, 131K ctx, 18.6 GB) via Ollama |
| NLU classifier | `llama3.1:8b` |
| Python | 3.14.5 (`adwi/.venv` via uv) |

---

## AUTHORITATIVE SOURCE PRECEDENCE

When sources conflict, resolve in this order:

1. **Runtime code** — `adwi/adwi_cli.py`, `adwi/path_validator.py`, `adwi/capabilities.json`
2. **Config files** — `local-ai-stack/docker-compose.yml`, `~/Library/LaunchAgents/com.suneel.*.plist`
3. **Generator output** — `adwi/system_manifest.json` (produced by `bin/generate-manifest`)
4. **README AUTO: sections** — machine-injected by `bin/auto-update-readme`
5. **CLAUDE.md** — manually maintained, verified by human
6. **README static sections** (§6 directory tree, §7–§10) — may lag; verify against code
7. **MASTER_REPORT_v2.md** — STALE (shows 89.0% from 2026-06-16; current baseline is 97.0%)

---

## CURRENT SYSTEM STATE (authoritative values — 2026-06-17)

### Models

| Constant | Model ID | Role |
|----------|----------|------|
| `MODEL_MAIN` | `adwi:latest` | Primary reasoning (qwen3:30b base) |
| `MODEL_FAST` | `llama3.1:8b` | NLU intent classification |
| `MODEL_NLU_FALLBACK` | `qwen3:0.6b` | NLU fallback when llama3.1 unavailable |
| `MODEL_VISION` | `minicpm-v:latest` | Vision / image analysis |
| `MODEL_EMBED` | `nomic-embed-text` | Embeddings (768-dim, memory/RAG) |

### NLU Pipeline

- **Intent classes:** 109 (from `_ALL_INTENTS` in `adwi/adwi_cli.py`)
- **Qdrant fixtures:** 96 (live in `nlu_fixtures` collection at :6333)
- **Fast-path threshold:** Qdrant score ≥ 0.88 → skip llama3.1:8b entirely (~5 ms vs 43 ms)
- **Current pass rate:** P1 96.7% · P2 98.2% · Combined **97.0%** (Stop Condition A met 2026-06-17)

Pipeline stages (every natural-language input):
1. Regex pre-filter (`_REGEX_INTENTS`) — zero latency
2. Qdrant few-shot lookup — top-3 of 96 fixtures
3. `llama3.1:8b` with JSON schema → `{analysis, confidence, intent, arguments}`
4. Fallback: `qwen3:0.6b`

### Command Registry

- **Total commands:** 167 (extracted from `adwi/adwi_cli.py` + `adwi/capabilities.json`)
- **Source of truth:** `bin/auto-update-readme` extractor → `README.md AUTO:COMMANDS`

### Services and Ports

| Port | Service | Layer |
|------|---------|-------|
| :11434 | Ollama | Host (brew) |
| :3000 | Open WebUI | Docker |
| :5055 | Safe Command API | Host |
| :5056 | Obsidian Bridge | Host (LaunchAgent) |
| :5678 | n8n | Docker |
| :6006 | Arize Phoenix | Host (LaunchAgent) |
| :6333 | Qdrant | Docker container started by LaunchAgent |
| :8123 | Home Assistant | Docker |
| :8888 | SearXNG | Docker |
| :9090 | Prometheus | Docker |
| :3100 | Loki | Docker |
| :4000 | Grafana | Docker |

### LaunchAgents (auto-start at login)

| Agent | Schedule | Purpose |
|-------|----------|---------|
| `adwi-git-backup` | every 30 min | Git backup |
| `adwi-nightly` | 2:00 AM | Maintenance loop |
| `adwi-scheduled-send` | every 2 min | Gmail scheduled-send runner |
| `phoenix` | KeepAlive | OTel observability UI |
| `obsidian-bridge` | KeepAlive | Vault HTTP API |
| `openwebui-knowledge-watcher` | KeepAlive | Sync Obsidian → Open WebUI |
| `qdrant` | RunAtLoad | `docker start suneel-qdrant` |
| `caffeinate` | KeepAlive | Prevent sleep |

---

## HARD SAFETY INVARIANTS

These rules are absolute. No exception, no workaround, no human confirmation possible:

1. **`PathValidator` blocks** (deny-first, checked before any allowed root):
   `secrets/`, `~/.ssh`, `~/.gnupg`, `~/.aws`, `~/.kube`, `~/.config/gcloud`,
   `~/.npmrc`, `~/.netrc`, `~/Library/Keychains`, `~/Library/Passwords`,
   `/etc`, `/private`, `/System`, `/usr/lib`

2. **`_REGEX_INTENTS` ordering is load-bearing.** First match wins. Adding a pattern in the wrong position breaks routing for every intent that follows it.

3. **`SimLab Tier C` is never auto-applied.** Any change touching safety/security logic requires explicit human git commit.

4. **Never commit:** `secrets/`, `config/.env`, `**/*token*`, `**/*.key`, `**/gmail-token.json`, `adwi/memory.db`, `adwi/knowledge.db`, `adwi/.venv/`

5. **Eval scripts must never import `adwi_cli.py`** — standalone harnesses only.

6. **`logs/`** is the eval evidence chain — do not delete or truncate.

---

## WHAT NOT TO ASSUME

If you are a cold-starting LLM, do NOT assume:

- `MASTER_REPORT_v2.md` is current — it shows 89.0% from 2026-06-16 and is **stale**. Use CLAUDE.md for current eval baseline.
- "62 intent classes" — that was the count when capabilities.json had 62 entries. `_ALL_INTENTS` now has **109** classes.
- "104-command registry" — was the Phase 5 count. Current count is **167**.
- "49-fixture nlu_fixtures" — was the Phase 7 initial count. Current live count is **96**.
- "89 NLU fixtures" — was an intermediate count. Current is **96**.
- "121 commands" — was an old annotation in the directory tree. Current is **167**.
- "35 helper scripts" — was stale bin/ count. Current is **41**.
- Docker SERVICES section ports were reliable before 2026-06-17 — a regex bug caused `:1` to appear for all ports; this is now fixed.
- README is fully auto-generated — only the `<!-- AUTO:... -->` sections are machine-maintained; §6 directory tree and narrative sections are manually maintained and may be slightly behind.

---

## CANONICAL FILES AND THEIR ROLES

| File | Role | Maintained by |
|------|------|--------------|
| `adwi/adwi_cli.py` | REPL, commands, NLU pipeline | Human + aider |
| `adwi/capabilities.json` | Capability registry (62 high-level entries) | Human |
| `adwi/path_validator.py` | Security gate — blocked roots | Human |
| `adwi/system_manifest.json` | Machine-readable ground truth snapshot | `bin/generate-manifest` |
| `local-ai-stack/docker-compose.yml` | Docker service definitions | Human |
| `~/Library/LaunchAgents/com.suneel.*.plist` | Launch agent schedules | Human |
| `README.md` | Architecture blueprint (AUTO + static sections) | `bin/auto-update-readme` + Human |
| `CLAUDE.md` | AI session orientation + current NLU baseline | Human |
| `docs/LLM_SYSTEM_PRIMING.md` | This file — cold-start model priming | Human (updated after major changes) |
| `docs/OPERATOR_HANDBOOK.md` | Human operator quick-reference | Human |
| `logs/simeval/MASTER_REPORT_v2.md` | NLU eval report — **STALE** (2026-06-16) | Eval harness |

---

## HOW TO REASON WHEN DOCS CONFLICT

```
Step 1: Check if the value is in an AUTO: section of README.md.
        → If yes: trust it (generated from live sources by bin/auto-update-readme).

Step 2: Check adwi/system_manifest.json (generated_at timestamp tells you freshness).
        → More recent than README? Trust manifest. Stale by >24h? Run bin/generate-manifest.

Step 3: Check adwi/adwi_cli.py or the relevant canonical source file directly.
        → This is always authoritative over any doc.

Step 4: If still ambiguous, grep the code and verify manually.
        → Document the conflict in docs/README_INCONSISTENCY_CHECKLIST.md.
```

---

## COLD-START CHECKLIST

Before making any change to NLU, commands, or infrastructure:

- [ ] Read `adwi/adwi_cli.py` lines 503–660 (`_REGEX_INTENTS`) — ordering is critical
- [ ] Read `adwi/adwi_cli.py` lines 865–1020 (`_INTENT_SYSTEM`) — LLM classification prompt
- [ ] Read `adwi/path_validator.py` — never weaken the gate
- [ ] Run `python3 -m py_compile adwi/adwi_cli.py && echo OK` — syntax check first
- [ ] Run `python3 -m unittest adwi/simlab/tests/test_nlu_regex.py` — 390 tests, should be 0 failures
- [ ] Run `python3 bin/validate-docs` — 0 FAIL before and after your change
- [ ] Sync changes to all 3 files: `adwi/adwi_cli.py`, `logs/simeval/run_large_eval.py`, `logs/simeval/run_large_eval_p2.py`

After significant changes:
- [ ] Run `bin/auto-update-readme --force` — regenerate README AUTO: sections
- [ ] Run `bin/generate-manifest` — update system_manifest.json
- [ ] Run `bin/validate-docs` — confirm 0 FAIL

---

## ARCHITECTURE IN COMPACT FORM

```
User input
  │
  ├── Slash command? ──────────────────────────────► Direct dispatch
  │
  ├── Regex match (_REGEX_INTENTS) ───────────────► Direct dispatch  (0 ms)
  │
  ├── Qdrant score ≥ 0.88 (nlu_fast_path.py) ──► Direct dispatch  (~5 ms)
  │
  └── llama3.1:8b classification (~43 ms)
        │
        └── JSON: {analysis, confidence, intent, arguments}
              │
              ├── File ops ──► PathValidator ──► BLOCKED / allowed
              ├── Git/system ─► Phase 2 LangGraph permission gate
              │                   Planner → Executor → Critic
              └── Safe ops ──► Direct execution
```

Nightly automation (2 AM via LaunchAgent):
```
nightly.py: cleanup → knowledge index → eval → backup → Obsidian daily note
```
