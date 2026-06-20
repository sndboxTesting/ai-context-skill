# Adwi Bootstrap Checklist

Print this or open it side-by-side when setting up a new machine.
Check each item before proceeding to the next. See `docs/SETUP_NEW_MACHINE.md` for the full guide.

---

## Phase 1 — Base system

- [ ] macOS 14+ confirmed (`sw_vers`)
- [ ] Homebrew installed (`brew --version`)
- [ ] Docker Desktop installed and running (`docker ps`)
- [ ] Git configured (`git config --global user.name`)
- [ ] `uv` installed (`uv --version`)
- [ ] Repo cloned to `~/SuneelWorkSpace/`
- [ ] `~/SuneelWorkSpace/bin` added to `$PATH` in `~/.zshrc`
- [ ] `which adwi` resolves correctly

## Phase 2 — Python

- [ ] `adwi/.venv/` created (`uv venv --python 3.12+`)
- [ ] Core packages installed: `prompt_toolkit`, `instructor`, `openai`, `qdrant-client`
- [ ] Optional packages installed: `faster-whisper`, `markitdown`, `opentelemetry-sdk`
- [ ] Syntax check: `python3 -m py_compile adwi/adwi_cli.py && echo OK`

## Phase 3 — Ollama + models

- [ ] Ollama installed (`brew install ollama`)
- [ ] Ollama running (`curl http://localhost:11434/api/tags`)
- [ ] `llama3.1:8b` pulled (`ollama pull llama3.1:8b`)
- [ ] `nomic-embed-text` pulled (`ollama pull nomic-embed-text`)
- [ ] `qwen3:0.6b` pulled (`ollama pull qwen3:0.6b`)
- [ ] `qwen3:30b` pulled (base for custom model)
- [ ] `adwi:latest` built (`ollama create adwi:latest -f adwi/Modelfile`)
- [ ] (Optional) `minicpm-v:latest` pulled for vision features

## Phase 4 — Config / secrets

- [ ] `config/.env` created from `config/.env.example`
- [ ] `TAVILY_API_KEY` set (or accepted as missing — optional)
- [ ] `HA_TOKEN` + `HA_URL` set (or accepted as missing — optional)
- [ ] `EXA_API_KEY` set (or accepted as missing — optional)
- [ ] `BRAVE_SEARCH_API_KEY` set (or accepted as missing — optional)
- [ ] `secrets/` directory exists and is gitignored (`git check-ignore secrets/`)

## Phase 5 — Docker services

- [ ] `cd local-ai-stack && docker compose up -d` succeeded
- [ ] Qdrant responding: `curl http://localhost:6333/`
- [ ] SearXNG responding: `curl "http://localhost:8888/search?q=test&format=json"`
- [ ] Open WebUI responding: `curl -I http://localhost:3000`
- [ ] n8n responding: `curl -I http://localhost:5678`

## Phase 6 — Supporting services

- [ ] Obsidian bridge started: `curl http://localhost:5056/`
- [ ] Safe Command API started: `curl http://localhost:5055/status-ai`
- [ ] (Optional) Arize Phoenix started: `bin/start-phoenix`

## Phase 7 — NLU and memory

- [ ] NLU fixtures provisioned: `python3 adwi/memory.py provision-nlu`
- [ ] Qdrant `nlu_fixtures` collection has ~89 points
- [ ] (Optional) memory.db rebuilt: `/memory-scan` in adwi REPL
- [ ] (Optional) knowledge.db rebuild started in background

## Phase 8 — LaunchAgents (production use)

- [ ] `adwi → /backup-enable` installs backup LaunchAgent
- [ ] `launchctl list | grep com.suneel` shows agents loaded
- [ ] 30-min backup agent running
- [ ] Nightly 2 AM agent scheduled

## Phase 9 — Auth / integrations

- [ ] Gmail auth complete (`adwi → /gmail-auth`) — or skipped
- [ ] n8n workflows imported from old machine — or skipped
- [ ] Cloudflare Tunnel configured — or skipped (dev only)
- [ ] Home Assistant integration verified — or skipped

## Phase 10 — Final validation

- [ ] `python3 scripts/validate_adwi_env.py` — all pass or acceptable warns
- [ ] `adwi → /doctor` passes
- [ ] `adwi → /status` shows services up
- [ ] `adwi → /model-status` shows correct model
- [ ] `adwi → /capabilities` loads cleanly
- [ ] At least one natural-language command routes correctly (e.g., "check my disk")

---

## Quick re-validation after changes

After any code change, run:
```bash
python3 -m py_compile adwi/adwi_cli.py && echo "syntax OK"
python3 scripts/validate_adwi_env.py
adwi → /doctor
```

After any NLU change, also run:
```bash
python3 logs/simeval/run_large_eval.py --workers 5
# Compare pass rate to baseline 75.8%
```
