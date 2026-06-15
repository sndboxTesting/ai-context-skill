# Troubleshooting Log

**Purpose:** Running record of issues encountered and their resolutions. Append new entries at the bottom.

---

## Template

```
### YYYY-MM-DD — [Short Title]
**Symptom:** What failed or behaved unexpectedly.
**Root Cause:** What actually caused it.
**Fix Applied:** What was done to resolve it.
**Prevention:** What was changed to prevent recurrence.
```

---

## 2026-06-15 — overnight_learn.py JSON parse failures

**Symptom:** Hundreds of "No JSON array found in response" warnings in `/tmp/overnight-learn.log`. Only 5 files indexed in 7 hours despite 146 eligible files.

**Root Cause:** Regex `r"\[[\s\S]*?\]"` was non-greedy. When adwi:latest prepended prose before the JSON array (e.g., "Here is the JSON: [...]"), the `*?` matched the shortest `[...]` — often an empty bracket inside an answer string, not the full Q&A array.

**Fix Applied:** Changed to greedy match `r"\[[\s\S]*\]"` in `adwi/overnight_learn.py:354`.

**Prevention:** Use greedy extraction for top-level JSON structures. Added retries with temperature reduction on parse failure.

---

## 2026-06-15 — adwi-evolution-loop.py and overnight_learn.py at workspace root

**Symptom:** Two large Python scripts (53KB, 33KB) sitting at the workspace root, polluting the top-level namespace. `__pycache__/` also at root.

**Root Cause:** Scripts were written to root without a home directory.

**Fix Applied:** Moved both to `adwi/`. Created root symlink for `overnight_learn.py` while a pending nohup was in flight; symlink removed after run completed.

**Prevention:** All adwi Python scripts go in `adwi/`. Updated `.gitignore` to exclude `adwi/knowledge.db`, `adwi/memory.db`, `adwi/rag-db/`.

---

## 2026-06-15 — SearXNG running on :8888, not :8080 or :8088

**Symptom:** SearXNG health checks against :8080 and :8088 returned nothing. Caused confusion in documentation.

**Root Cause:** `docker-compose.yml` maps container port 8080 → host port 8888. Host port is 8888.

**Fix Applied:** Updated all adwi_cli.py references and config/.env to use `:8888`. Noted in Local AI Stack Overview.

**Prevention:** Reference the docker-compose.yml port mapping as the source of truth.

---
<!-- Add new entries above this line -->
