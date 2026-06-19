# Adwi NLU — Master Eval Report v2
*Generated: 2026-06-19 10:53 | Sessions: large-20260619-103709, large-p2-20260619-104828*

---
## 1. Run Summary
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Total scenarios | 2283 | +1781 |
| Pass | 2246 (98.4%) | was 75.5% |
| Warn | 11 | — |
| Fail | 26 | — |
| Errors (LLM/parse) | 1 | — |
| Regex fast-path | 1526 (66.8%) | was 43.4% |
| LLM calls | 756 | — |
| Avg latency | 3959.4ms | — |
| P95 latency | 13846.4ms | — |
| Safety probes | 66 | — |
| Safety breaches | 0 | — |

---
## 2. Category Pass Rates
| Category | Pass | Total | Rate |
|----------|------|-------|------|
| comms | 419 | 422 | 99.3% |
| system | 257 | 261 | 98.5% |
| disk | 247 | 252 | 98.0% |
| repair | 232 | 236 | 98.3% |
| chat | 178 | 186 | 95.7% |
| git | 113 | 113 | 100.0% |
| search | 102 | 104 | 98.1% |
| memory | 98 | 99 | 99.0% |
| media | 90 | 90 | 100.0% |
| file | 85 | 88 | 96.6% |
| safety | 66 | 66 | 100.0% |
| vault | 63 | 64 | 98.4% |
| model | 57 | 58 | 98.3% |
| voice | 46 | 46 | 100.0% |
| planning | 42 | 44 | 95.5% |
| ambiguous | 38 | 39 | 97.4% |
| upgrade_pack | 35 | 35 | 100.0% |
| meta | 29 | 31 | 93.5% |
| eval | 28 | 28 | 100.0% |
| security | 19 | 19 | 100.0% |
| exec | 2 | 2 | 100.0% |

---
## 3. Failure Families

### `chat` — 7 failures → rag_search(3), memory_recall(2), sync(1)
  - `what is the difference between qdrant and pinecone`
  - `sync everything`
  - `remember this for me`
  - `what else can adwi do`

### `old_files` — 2 failures → memory_scan(1), large_files(1)
  - `what hasn't been used in 2 years`
  - `files untouched for months`

### `file_search` — 2 failures → obsidian_search(1), backup_now(1)
  - `find all dockerfile variants`
  - `find backup scripts`

### `__none__` — 2 failures → __none__(1), doctor(1)
  - `export training data`
  - `learn from my last error`

### `large_files` — 1 failures → disk_usage(1)
  - `size hogs on my disk`

### `status` — 1 failures → chat(1)
  - `all ok?`

### `file_list` — 1 failures → file_search(1)
  - `what's in my home directory`

### `gmail_tasks_save` — 1 failures → obsidian_daily(1)
  - `add those to my daily note`

### `gmail_confirm` — 1 failures → chat(1)
  - `do it`

### `disk_usage` — 1 failures → chat(1)
  - `show me the data`

### `gmail` — 1 failures → gmail_thread_intel(1)
  - `check my email then search for any action items`

### `nightly_run` — 1 failures → nightly_status(1)
  - `rn nightly`

### `use_local` — 1 failures → use_cloud(1)
  - `i need to switch from the cloud model to a local one because i'm offline right n`

### `benchmark` — 1 failures → chat(1)
  - `my local AI model is responding much slower than usual what could be causing thi`

### `fix_error` — 1 failures → __none__(1)
  - `help: NotImplementedError: subclasses must implement process()`

### `web_search` — 1 failures → rag_search(1)
  - `search with tavily for python packages`

### `obsidian_search` — 1 failures → memory_recall(1)
  - `notes`

---
## 4. Top Mis-routes (expected → got)
| Pattern | Count |
|---------|-------|
| `chat` → `rag_search` | 3 |
| `chat` → `memory_recall` | 2 |
| `large_files` → `disk_usage` | 1 |
| `old_files` → `memory_scan` | 1 |
| `old_files` → `large_files` | 1 |
| `status` → `chat` | 1 |
| `file_list` → `file_search` | 1 |
| `file_search` → `obsidian_search` | 1 |
| `file_search` → `backup_now` | 1 |
| `gmail_tasks_save` → `obsidian_daily` | 1 |
| `gmail_confirm` → `chat` | 1 |
| `chat` → `sync` | 1 |
| `chat` → `what_next` | 1 |
| `disk_usage` → `chat` | 1 |
| `gmail` → `gmail_thread_intel` | 1 |
| `nightly_run` → `nightly_status` | 1 |
| `use_local` → `use_cloud` | 1 |
| `__none__` → `__none__` | 1 |
| `benchmark` → `chat` | 1 |
| `__none__` → `doctor` | 1 |
| `fix_error` → `__none__` | 1 |
| `web_search` → `rag_search` | 1 |
| `obsidian_search` → `memory_recall` | 1 |

---
## 5. Unstable Paraphrase Families (top 20)
| Family | Consistency | Pass/Total |
|--------|-------------|------------|
| gmail_confirm | 80.0% | 4/5 |
| gmail_tasks_save | 87.5% | 7/8 |

---
## 6. Safety Summary
✅ No safety breaches detected.

---
## 7. Needs Human Review — Proposed Fixes

### FIX-003: obsidian_search/daily → memory_recall LLM confusion
**Impact:** ~1 scenarios | **Effort:** low | **Confidence:** medium

**Root Cause:** LLM sees 'search my notes', 'open my note', 'my daily note' and routes to memory_recall because _INTENT_SYSTEM description for memory_recall says 'what YOU remember about their setup'. Notes queries are semantically similar to memory queries.

**Proposed Fix:**
```
Strengthen _INTENT_SYSTEM: add to obsidian_search rule: 'ALWAYS prefer obsidian_search over memory_recall when the prompt mentions obsidian, vault, or notes with a search action'. Also add: for memory_recall, explicitly say NOT for obsidian/vault/note search queries.
```

**File:** `adwi/adwi_cli.py — _INTENT_SYSTEM`

**Evidence:**
  - `notes`

### FIX-004: large_files → disk_usage regression for some prompts
**Impact:** ~1 scenarios | **Effort:** low | **Confidence:** medium

**Root Cause:** Some large_files prompts contain 'disk' or 'space' keywords which trigger disk_usage regex. Example: 'what's the heaviest stuff on disk' — correctly routes to disk_usage, but 'heaviest files on disk' should route to large_files.

**Proposed Fix:**
```
Add additional large_files pattern: `\bfiles?\b.{0,30}(heaviest|biggest|largest|most space).{0,20}(disk|drive|ssd)` → large_files BEFORE disk_usage patterns.
```

**File:** `adwi/adwi_cli.py — _REGEX_INTENTS`

**Evidence:**
  - `size hogs on my disk`

### FIX-006: benchmark regex too narrow — misses 'how fast is my model'
**Impact:** ~1 scenarios | **Effort:** low | **Confidence:** high

**Root Cause:** Current benchmark regex requires 'adwi|model|local|ollama' in the same phrase as 'benchmark|speed test|how fast|tokens per second'. Many benchmark prompts like 'tokens/sec please', 't/s benchmark', 'inference throughput' don't have these keywords.

**Proposed Fix:**
```
Add: `(tokens?/s|t/s|tok/s|throughput).{0,20}(model|llm|ollama|adwi)?` → benchmark
And: `(inference|llm|model|ollama).{0,20}(speed|throughput|latency|benchmark)` → benchmark
And: `how fast.{0,20}(llm|model|is adwi|is ollama)` → benchmark
```

**File:** `adwi/adwi_cli.py — _REGEX_INTENTS`

**Evidence:**
  - `my local AI model is responding much slower than usual what could be causing this and how do i benchmark it`

---
## 8. Prioritized Repair Backlog
Ordered by (estimated_impact × confidence / effort):

1. **FIX-003** — obsidian_search/daily → memory_recall LLM confusion (~1 scenarios)
2. **FIX-004** — large_files → disk_usage regression for some prompts (~1 scenarios)
3. **FIX-006** — benchmark regex too narrow — misses 'how fast is my model' (~1 scenarios)

---
## 9. Regex Fast-Path Coverage by Intent
| Intent | Regex hits |
|--------|-----------|
| fix_error | 113 |
| chat | 49 |
| gmail | 47 |
| web_search | 43 |
| cleanup | 39 |
| large_files | 37 |
| self_heal | 37 |
| git_status | 37 |
| __none__ | 36 |
| disk_usage | 35 |
| duplicates | 33 |
| file_search | 33 |
| organize | 28 |
| benchmark | 28 |
| obsidian_search | 28 |
| old_files | 25 |
| obsidian_daily | 25 |
| rag_search | 24 |
| status | 23 |
| generate_image | 23 |
| browse | 21 |
| memory_scan | 20 |
| what_next | 19 |
| nightly_status | 19 |
| model_status | 19 |
| memory_recall | 19 |
| patch_adwi | 19 |
| doctor | 18 |
| file_read | 18 |
| gmail_rewrite_draft | 18 |
| voice_in | 17 |
| gmail_thread_intel | 16 |
| gmail_extract_tasks | 16 |
| gmail_filter_build | 15 |
| voice_out | 15 |
| gmail_triage | 14 |
| youtube | 14 |
| backup_status | 14 |
| gmail_compose | 13 |
| gmail_send_draft | 13 |
| memory_stats | 13 |
| file_list | 12 |
| gmail_summarize | 12 |
| gmail_schedule_send | 12 |
| use_local | 11 |
| github_connected | 11 |
| use_cloud | 10 |
| gmail_list_category | 10 |
| gmail_attach_file | 10 |
| backup_log | 10 |
| eval_adwi | 10 |
| test_adwi | 10 |
| gmail_undo | 9 |
| eval_routing | 9 |
| gmail_draft_reply | 8 |
| gmail_update_subject | 8 |
| gmail_open_draft | 8 |
| gmail_reschedule_send | 8 |
| capabilities | 8 |
| sync | 8 |
| gmail_read | 7 |
| gmail_archive | 7 |
| gmail_trash | 7 |
| gmail_followup_reminder | 7 |
| gmail_list_followups | 7 |
| gmail_list_drafts | 7 |
| gmail_forward | 7 |
| gmail_tasks_save | 7 |
| gmail_tasks_remind | 7 |
| inspect_code | 7 |
| research | 7 |
| browser_delegate | 7 |
| memory_context | 7 |
| gmail_open | 6 |
| gmail_thread | 6 |
| gmail_show_draft | 6 |
| gmail_add_cc | 6 |
| gmail_add_bcc | 6 |
| gmail_list_attachments | 6 |
| gmail_save_attachment | 6 |
| gmail_summarize_attachment | 6 |
| gmail_remove_attachment | 6 |
| gmail_open_scheduled_draft | 6 |
| nightly_run | 5 |
| gmail_mark_read | 5 |
| gmail_cancel | 5 |
| gmail_cancel_draft | 5 |
| gmail_cancel_followup | 5 |
| gmail_delete_draft | 5 |
| gmail_filter_apply | 5 |
| trusted_roots | 5 |
| extract_ideas | 5 |
| daily_brief | 5 |
| tech_radar | 5 |
| memory_curate | 5 |
| gmail_mark_unread | 4 |
| gmail_confirm | 4 |
| gmail_filter_cancel | 4 |
| gmail_filter_list | 4 |
| implement_idea | 4 |
| gmail_list_scheduled | 3 |
| gmail_cancel_scheduled_send | 3 |
| run_code | 3 |
| tool_roadmap | 3 |
| assistant_upgrade_status | 3 |
| route | 2 |
| daily_improve | 1 |

---
## 10. Latency Hotspots (top 15 slowest LLM calls)
  - 18371ms | `help: OverflowError: int too large to convert to float`
  - 17773ms | `pandas.errors.EmptyDataError fix this`
  - 17419ms | `how do i fix sqlalchemy.exc.IntegrityError: UNIQUE constrain`
  - 17403ms | `help: subprocess.CalledProcessError: Command 'git push' retu`
  - 17317ms | `help: sqlalchemy.exc.IntegrityError: UNIQUE constraint faile`
  - 17278ms | `help: redis.exceptions.ResponseError: WRONGTYPE Operation`
  - 17266ms | `help: docker.errors.NotFound: 404 Container not found`
  - 17243ms | `how do i fix redis.exceptions.ResponseError: WRONGTYPE Opera`
  - 17239ms | `how do i fix subprocess.CalledProcessError: Command 'git pus`
  - 17069ms | `how full is my hard drive`
  - 17021ms | `fastapi.exceptions.HTTPException: 422`
  - 17016ms | `subprocess.CalledProcessError: returned non-zero exit`
  - 16979ms | `sqlalchemy.exc.OperationalError fix`
  - 16928ms | `what's stored in memory about my projects`
  - 16889ms | `boto3.exceptions.Boto3Error how to resolve`