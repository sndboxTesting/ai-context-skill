# Adwi Mistakes and Fixes

Every time something fails, this file logs: what was asked, what was tried, the error, the fix, and the rule to remember.
Updated by `/daily-improve` and error handlers in adwi_cli.py.

---

## 2026-06-14 — Context Window Default

**What was asked:** Use adwi for long conversations and document analysis

**What was tried:** Running adwi with default Ollama settings

**Error:** Context silently truncated at 2,048 tokens — conversations lost memory after ~1,500 words

**Fix:** Added `PARAMETER num_ctx 131072` to Modelfile and rebuilt adwi with `ollama create adwi -f Modelfile`

**Rule to remember:** Always set `num_ctx` explicitly. Never assume Ollama uses the model's advertised max context.

---

## 2026-06-14 — Summarize Scripts Used Wrong Model

**What was asked:** Summarize YouTube videos

**What was tried:** `summarize-youtube` and `summarize-url` scripts called `llama3.1:8b`

**Error:** Smaller model gave weaker summaries; adwi:latest (30.5B) was not being used

**Fix:** Updated both scripts to call `adwi:latest` via Ollama API

**Rule to remember:** When installing a new primary model, update ALL scripts that hardcode model names.

---
