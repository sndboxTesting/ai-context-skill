# Adwi — Claude Session Orientation

> **Read this first** if you are a Claude session (or any AI model) starting work in this repo.
> This file is the fastest path from a cold start to productive contributions.

---

## What this repo is

Adwi is a local AI operating system running on an Apple Silicon Mac. It is not a library or API — it is a personal AI assistant that operates as a terminal REPL and a set of daemon services. The operator is Suneel Bikkasani.

**Entry point:** `adwi/bin/adwi` → `python3 adwi/adwi_cli.py`

**Primary model:** `adwi:latest` (qwen3:30b via Ollama, 131K context, 64 GB RAM)

**NLU classifier:** `llama3.1:8b` — classifies every natural-language input into one of 109 intent classes before dispatch.

---

## Before touching any file, read these

| File | Why |
|------|-----|
| `README.md` §5 | Security invariants and hard-blocked paths — never bypass these |
| `adwi/path_validator.py` | Deny-first path guard — understand before any file operation |
| `adwi/adwi_cli.py` lines 503–660 | `_REGEX_INTENTS` — NLU fast path, ordering is critical |
| `adwi/adwi_cli.py` lines 865–1020 | `_INTENT_SYSTEM` — LLM classification prompt |
| `adwi/logs/simeval/MASTER_REPORT_v2.md` | ⚠️ STALE (89.0%, 2026-06-16) — historical baseline only. Current state is in the table below. |
| `adwi/docs/NLU_REPAIR_BACKLOG.md` | Prioritized fix list with exact code proposals |

---

## Current NLU quality (as of 2026-06-17)

| Eval | Scenarios | Pre-NHR | Stabilize sprint | CYCLE-5 | CYCLE-6 | Total gain |
|------|-----------|---------|------------------|---------|---------|------------|
| Large eval P1 | ~1,808 | 78.0% | 92.6% | 96.3% | **96.7%** | +18.7pp |
| Large eval P2 (weak-family targeting) | 561 | 68.6% | 88.8% | 97.0% | **98.2%** | +29.6pp |
| **Combined** | **~2,369** | **75.8%** | **~91.7%** | **~96.5%** | **~97.0%** | **+21.2pp** |

**Stop Condition A reached 2026-06-17: combined >95%. All 10 NHR items applied 2026-06-16. Sessions 2-4 applied 2026-06-16. Gmail burn-in + stabilization sprint applied 2026-06-17. CYCLE-5 (2026-06-17): 13 bare-command anchors, chat advisory fixes, status/advisory boundary, memory_scan/github_connected/web_search additions — synced to all 3 files. CYCLE-6 (2026-06-17): PermissionError guard before CYCLE-1, run-aider before self-heal, organize before chat, use_local/large_files/gmail_list_attachments/capabilities/trusted_roots/tool_roadmap/test_adwi targeted fixes — synced to all 3 files.**

Session-2 applied 11 regex patch groups (FIX-LF-001, FIX-OLD-001, FIX-DUP-001, FIX-ORG-002, FIX-CLEANUP-003, FIX-HEAL-001, FIX-BROWSE-001, FIX-WEB-001, FIX-ERR-002, FIX-EVAL-002, FIX-TEST-002, FIX-MEMSCAN-002) and 1 INTENT_SYSTEM clarification (FIX-BENCH-001).

Session-3 applied 9 regex patch groups (FIX-CLEAN-004, FIX-NOTES-001, FIX-STATUS-002, FIX-WHAT-002, FIX-WEB-002, FIX-OBS-002, FIX-NIGHT-001, FIX-EVAL-003, FIX-PATCH-002, FIX-RC-001, FIX-GMAIL-002, FIX-MEMST-001, FIX-MEMCTX-001, FIX-FR-001) and S3 fixes (FIX-S3-001 through FIX-S3-009) and 4 INTENT_SYSTEM clarifications.

Session-4 applied 8 false-positive hardening fixes. Gmail burn-in applied 12 FIX-STRESS patches + 4 FIX-STAGE3 patches. Stabilization sprint applied 9 regex fix groups + 4 _INTENT_SYSTEM additions + 6 test gap fixes. Total test suite after CYCLE-6: 897 tests.

**Current baseline: ~97.0% combined.** Remaining P1 failures (~40): ~11 LLM-routed chat bleed, irreducible __none__ safety blocks, scattered LLM variance. P2 has zero hard failures (551/561 pass, 10 warns).

Changes are synchronized across all 3 files: `adwi/adwi_cli.py`, `adwi/logs/simeval/run_large_eval.py`, `adwi/logs/simeval/run_large_eval_p2.py`.

---

## Key invariants — never violate

1. **`_REGEX_INTENTS` ordering is load-bearing.** First match wins. New patterns must go before the intents they must beat.
2. **`BLOCKED_PATHS` is execution-layer safety.** NLU routing to `file_read` for a blocked path is not a breach — the gate stops execution. Do not weaken the gate.
3. **SimLab never auto-applies Tier C.** Safety/security changes always require human review.
4. **`secrets/` is gitignored entirely.** Never suggest committing anything from there.
5. **`adwi/config/.env` is gitignored.** `adwi/config/.env.example` is the commit-safe template.
6. **`adwi/memory.db` and `adwi/knowledge.db` are gitignored.** Regenerated on each machine.
7. **`aider` never touches secret files.** Validated before any file is passed to aider.

---

## File responsibility map

| File | Owns |
|------|------|
| `adwi/adwi_cli.py` | REPL, 167 commands, NLU pipeline (`_REGEX_INTENTS`, `_INTENT_SYSTEM`, dispatch), Phase 3 risk classifier, Phase 4 live self-heal |
| `adwi/reason_engine.py` | LangGraph Planner→Executor→Critic, permission gate, aider integration, AchievementLedger |
| `adwi/memory.py` | SQLite memory store, nomic-embed cosine search, Qdrant NLU fixtures, knowledge.db |
| `adwi/path_validator.py` | Deny-first path containment — blocks `~/.ssh`, `~/.aws`, `secrets/`, etc. |
| `adwi/nlu_fast_path.py` | Qdrant ≥0.88 score bypass — skips llama3.1:8b for high-confidence prompts |
| `adwi/nightly.py` | 10-step 2 AM maintenance loop (LaunchAgent) |
| `adwi/voice.py` | STT (faster-whisper) + TTS (piper-tts) |
| `adwi/backup.py` | Git backup orchestration |
| `adwi/simlab/` | Bounded continuous eval & self-improvement (11 modules) |
| `adwi/services/command-api/server.py` | Safe Command API :5055 (8 allowlisted routes for n8n/iPhone) |
| `adwi/services/mcp/obsidian-bridge/` | Vault HTTP CRUD API :5056 |
| `adwi/bin/` | 41 scripts (shell + Python helpers) |
| `adwi/logs/simeval/` | Large-scale eval artifacts (MASTER_REPORT_v2.md, fix_backlog_v2.json, jsonl results) |
| `adwi/config/.env` | [gitignored] API keys — never read by Claude, only loaded as env vars |
| `adwi/docs/` | Human + Claude onboarding documentation |

---

## How to make an NLU fix

1. Read `adwi/docs/NLU_REPAIR_BACKLOG.md` for the current NHR item list.
2. Identify which NHR item you are implementing.
3. Locate `_REGEX_INTENTS` in `adwi/adwi_cli.py` (line ~503). New patterns must go BEFORE any intent they should beat.
4. If adding an `_INTENT_SYSTEM` rule, locate the system prompt (line ~865) and add to the relevant intent's description.
5. After editing, run the fast syntax check: `python3 -m py_compile adwi/adwi_cli.py && echo OK`
6. Then run the eval harness: `python3 adwi/logs/simeval/run_large_eval.py --workers 5` (or a targeted P2 run)
7. Compare new pass rate to the **97.0% combined current baseline** (all NHR + CYCLE-5 + CYCLE-6 applied).
8. Mark the NHR item as applied in `adwi/docs/NLU_REPAIR_BACKLOG.md`.
9. If the session materially changes the pass rate, run `python3 adwi/logs/simeval/generate_master_report.py` with the new session paths to produce a fresh MASTER_REPORT. Update the table in this file.

---

## How to run the eval harness

```bash
# Fast syntax check first
python3 -m py_compile adwi/adwi_cli.py && echo "syntax OK"

# Requires Ollama running with llama3.1:8b
ollama list | grep llama3.1

# Full 1,444-scenario eval (takes ~20-30 min with 10 workers)
python3 adwi/logs/simeval/run_large_eval.py --workers 10

# Targeted P2 (446 scenarios, weak families only)
python3 adwi/logs/simeval/run_large_eval_p2.py --workers 10

# Combined analysis report
python3 adwi/logs/simeval/generate_master_report.py \
    adwi/logs/simeval/large-<date>-<time> \
    adwi/logs/simeval/large-p2-<date>-<time>
```

Results land in `adwi/logs/simeval/<session-dir>/results.jsonl`. The eval harness is standalone — it does not import `adwi_cli.py` and does not touch production data.

---

## What NOT to do

- Do not weaken `BLOCKED_PATHS`, `PathValidator`, or the `REVIEW-REQUIRED` tier in the risk classifier.
- Do not auto-commit or auto-push. Backup is triggered by `adwi/bin/adwi-git-backup` (runs every 30 min via LaunchAgent).
- Do not change the SimLab golden baseline (`adwi/simlab/golden_baseline.jsonl`) — it is immutable except via explicit human commit.
- Do not suggest checking in `adwi/config/.env`, any file from `secrets/`, or any `*token*` file.
- Do not import production `adwi_cli.py` from within an eval script — standalone eval harnesses only.
- Do not `rm -rf` or destructively modify `adwi/logs/` — it contains the eval evidence chain.

---

## How to bootstrap on a new machine

See `adwi/docs/SETUP_NEW_MACHINE.md` for the full guide.
Quick validation: `python3 adwi/scripts/validate_adwi_env.py`

---

## Repair log conventions

After making any change:
1. Update `adwi/notes/adwi-mistakes-and-fixes.md` if you fixed a bug.
2. Update `adwi/docs/NLU_REPAIR_BACKLOG.md` if you applied an NHR item.
3. Do NOT create loose analysis files in the root — put them in `adwi/docs/` (persistent) or `adwi/logs/simeval/` (eval artifacts).
