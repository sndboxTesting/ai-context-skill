# Adwi NLU — Master Eval Report v2
*Generated: 2026-06-18 10:24 | Sessions: large-20260618-100658, large-p2-20260618-100319*

---
## 1. Run Summary
| Metric | Value | vs Baseline |
|--------|-------|-------------|
| Total scenarios | 2283 | +1781 |
| Pass | 2187 (95.8%) | was 75.5% |
| Warn | 28 | — |
| Fail | 68 | — |
| Errors (LLM/parse) | 0 | — |
| Regex fast-path | 1498 (65.6%) | was 43.4% |
| LLM calls | 785 | — |
| Avg latency | 2124.0ms | — |
| P95 latency | 7053.3ms | — |
| Safety probes | 66 | — |
| Safety breaches | 0 | — |

---
## 2. Category Pass Rates
| Category | Pass | Total | Rate |
|----------|------|-------|------|
| comms | 415 | 422 | 98.3% |
| system | 254 | 261 | 97.3% |
| disk | 244 | 252 | 96.8% |
| repair | 226 | 236 | 95.8% |
| chat | 163 | 186 | 87.6% |
| git | 106 | 113 | 93.8% |
| search | 99 | 104 | 95.2% |
| memory | 95 | 99 | 96.0% |
| media | 89 | 90 | 98.9% |
| file | 84 | 88 | 95.5% |
| safety | 66 | 66 | 100.0% |
| vault | 64 | 64 | 100.0% |
| model | 57 | 58 | 98.3% |
| voice | 45 | 46 | 97.8% |
| planning | 39 | 44 | 88.6% |
| ambiguous | 33 | 39 | 84.6% |
| upgrade_pack | 34 | 35 | 97.1% |
| meta | 27 | 31 | 87.1% |
| eval | 27 | 28 | 96.4% |
| security | 18 | 19 | 94.7% |
| exec | 2 | 2 | 100.0% |

---
## 3. Failure Families

### `chat` — 21 failures → memory_recall(6), sync(2), patch_adwi(2)
  - `how do I set up tailscale`
  - `best alternative to notion`
  - `how do I protect my home network`
  - `what's a good backup strategy for a homelab`

### `status` — 3 failures → web_search(1), doctor(1), chat(1)
  - `is everything online`
  - `what's wrong`
  - `my model is slow what's wrong`

### `git_status` — 3 failures → chat(1), file_list(1), memory_recall(1)
  - `are there any changes`
  - `what's in staging`
  - `recent change history`

### `what_next` — 2 failures → memory_recall(1), capabilities(1)
  - `what's missing from adwi`
  - `what could adwi do that it can't now`

### `file_search` — 2 failures → obsidian_search(1), chat(1)
  - `find all dockerfile variants`
  - `locate the eval runner`

### `backup_status` — 2 failures → status(2)
  - `backup ok?`
  - `backip status`

### `inspect_code` — 2 failures → memory_recall(2)
  - `explain what memory.py does`
  - `inspect the memory module`

### `run_code` — 2 failures → chat(1), status(1)
  - `run it`
  - `run the thing`

### `nightly_status` — 2 failures → memory_curate(1), status(1)
  - `show me the logs`
  - `what was the last thing that ran`

### `__none__` — 2 failures → __none__(1), fix_error(1)
  - `export training data`
  - `learn from my last error`

### `disk_usage` — 1 failures → capabilities(1)
  - `show capacity`

### `file_read` — 1 failures → inspect_code(1)
  - `display adwi main file`

### `file_list` — 1 failures → file_search(1)
  - `what's in my home directory`

### `gmail_list_category` — 1 failures → obsidian_search(1)
  - `what's in my promotions`

### `gmail_tasks_save` — 1 failures → obsidian_daily(1)
  - `add those to my daily note`

### `gmail_confirm` — 1 failures → chat(1)
  - `do it`

### `gmail_add_cc` — 1 failures → chat(1)
  - `also cc my assistant`

### `gmail_add_bcc` — 1 failures → gmail(1)
  - `also bcc my boss`

### `gmail_save_attachment` — 1 failures → file_save(1)
  - `save the attached file`

### `web_search` — 1 failures → tech_radar(1)
  - `what's the latest in AI`

### `browse` — 1 failures → obsidian_search(1)
  - `browse obsidian.md`

### `memory_stats` — 1 failures → memory_recall(1)
  - `memory summary stats`

### `backup_now` — 1 failures → git_status(1)
  - `commit and backup`

### `voice_out` — 1 failures → daily_brief(1)
  - `speak the morning brief`

### `trusted_roots` — 1 failures → capabilities(1)
  - `what can adwi read`

---
## 4. Top Mis-routes (expected → got)
| Pattern | Count |
|---------|-------|
| `chat` → `memory_recall` | 6 |
| `backup_status` → `status` | 2 |
| `inspect_code` → `memory_recall` | 2 |
| `chat` → `sync` | 2 |
| `chat` → `patch_adwi` | 2 |
| `chat` → `what_next` | 2 |
| `chat` → `git_status` | 2 |
| `disk_usage` → `capabilities` | 1 |
| `status` → `web_search` | 1 |
| `what_next` → `memory_recall` | 1 |
| `what_next` → `capabilities` | 1 |
| `file_read` → `inspect_code` | 1 |
| `file_list` → `file_search` | 1 |
| `file_search` → `obsidian_search` | 1 |
| `file_search` → `chat` | 1 |
| `gmail_list_category` → `obsidian_search` | 1 |
| `gmail_tasks_save` → `obsidian_daily` | 1 |
| `gmail_confirm` → `chat` | 1 |
| `gmail_add_cc` → `chat` | 1 |
| `gmail_add_bcc` → `gmail` | 1 |
| `gmail_save_attachment` → `file_save` | 1 |
| `web_search` → `tech_radar` | 1 |
| `browse` → `obsidian_search` | 1 |
| `memory_stats` → `memory_recall` | 1 |
| `git_status` → `chat` | 1 |
| `git_status` → `file_list` | 1 |
| `git_status` → `memory_recall` | 1 |
| `backup_now` → `git_status` | 1 |
| `voice_out` → `daily_brief` | 1 |
| `trusted_roots` → `capabilities` | 1 |

---
## 5. Unstable Paraphrase Families (top 20)
| Family | Consistency | Pass/Total |
|--------|-------------|------------|
| gmail_confirm | 80.0% | 4/5 |
| research | 80.0% | 4/5 |
| gmail_add_cc | 83.3% | 5/6 |
| gmail_add_bcc | 83.3% | 5/6 |
| gmail_save_attachment | 83.3% | 5/6 |
| chat | 85.3% | 93/109 |
| gmail_tasks_save | 87.5% | 7/8 |
| test_adwi | 87.5% | 7/8 |

---
## 6. Safety Summary
✅ No safety breaches detected.

---
## 7. Needs Human Review — Proposed Fixes

### FIX-001: file_search regex too broad — swallows cleanup/duplicates/large_files
**Impact:** ~1 scenarios | **Effort:** low | **Confidence:** high

**Root Cause:** `\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b` matches 'find things to delete', 'find duplicate files', 'find large files'. The word 'files' appears in disk management prompts but should not trigger file_search.

**Proposed Fix:**
```
Add negative lookahead to file_search pattern: require file path context (extension, directory, 'in workspace', 'in /path') OR remove 'find' as standalone trigger. Alternative: add pre-guards for duplicate/cleanup intents BEFORE file_search in REGEX_INTENTS.
```

**File:** `adwi/adwi_cli.py — _REGEX_INTENTS file_search section`

**Evidence:**
  - `find dupkicates`

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

1. **FIX-001** — file_search regex too broad — swallows cleanup/duplicates/large_files (~1 scenarios)
2. **FIX-006** — benchmark regex too narrow — misses 'how fast is my model' (~1 scenarios)

---
## 9. Regex Fast-Path Coverage by Intent
| Intent | Regex hits |
|--------|-----------|
| fix_error | 113 |
| chat | 49 |
| gmail | 47 |
| cleanup | 39 |
| web_search | 39 |
| large_files | 37 |
| self_heal | 37 |
| git_status | 37 |
| disk_usage | 35 |
| file_search | 33 |
| __none__ | 33 |
| duplicates | 32 |
| obsidian_search | 29 |
| organize | 28 |
| benchmark | 28 |
| obsidian_daily | 25 |
| status | 23 |
| generate_image | 23 |
| old_files | 22 |
| rag_search | 22 |
| browse | 21 |
| memory_scan | 20 |
| what_next | 19 |
| model_status | 19 |
| memory_recall | 19 |
| doctor | 18 |
| nightly_status | 18 |
| file_read | 18 |
| gmail_rewrite_draft | 18 |
| patch_adwi | 18 |
| voice_in | 17 |
| gmail_thread_intel | 16 |
| gmail_extract_tasks | 16 |
| gmail_filter_build | 15 |
| gmail_triage | 14 |
| youtube | 14 |
| backup_status | 14 |
| voice_out | 14 |
| gmail_compose | 13 |
| gmail_send_draft | 13 |
| memory_stats | 13 |
| file_list | 12 |
| gmail_summarize | 12 |
| gmail_schedule_send | 12 |
| use_local | 11 |
| use_cloud | 10 |
| gmail_list_category | 10 |
| gmail_attach_file | 10 |
| backup_log | 10 |
| github_connected | 10 |
| eval_adwi | 10 |
| gmail_undo | 9 |
| eval_routing | 9 |
| test_adwi | 9 |
| gmail_draft_reply | 8 |
| gmail_update_subject | 8 |
| gmail_open_draft | 8 |
| gmail_reschedule_send | 8 |
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
| browser_delegate | 7 |
| memory_context | 7 |
| gmail_open | 6 |
| gmail_thread | 6 |
| gmail_show_draft | 6 |
| gmail_list_attachments | 6 |
| gmail_summarize_attachment | 6 |
| gmail_remove_attachment | 6 |
| gmail_open_scheduled_draft | 6 |
| daily_brief | 6 |
| capabilities | 6 |
| nightly_run | 5 |
| gmail_mark_read | 5 |
| gmail_cancel | 5 |
| gmail_cancel_draft | 5 |
| gmail_add_cc | 5 |
| gmail_add_bcc | 5 |
| gmail_save_attachment | 5 |
| gmail_cancel_followup | 5 |
| gmail_delete_draft | 5 |
| gmail_filter_apply | 5 |
| extract_ideas | 5 |
| tech_radar | 5 |
| memory_curate | 5 |
| gmail_mark_unread | 4 |
| gmail_confirm | 4 |
| gmail_filter_cancel | 4 |
| gmail_filter_list | 4 |
| implement_idea | 4 |
| research | 4 |
| gmail_list_scheduled | 3 |
| gmail_cancel_scheduled_send | 3 |
| run_code | 3 |
| tool_roadmap | 3 |
| assistant_upgrade_status | 3 |
| route | 2 |
| daily_improve | 1 |
| trusted_roots | 1 |

---
## 10. Latency Hotspots (top 15 slowest LLM calls)
  - 9317ms | `find obsidian notes on docker compose`
  - 9295ms | `find vault notes on productivity`
  - 8937ms | `look up notes on tailscale in obsidian`
  - 8918ms | `look in obsidian for home lab notes`
  - 8878ms | `git changes overview`
  - 8835ms | `what's my current git state`
  - 8648ms | `look for notes about n8n webhooks`
  - 8633ms | `push my changes to github`
  - 8620ms | `backup now`
  - 8363ms | `garbage collection for my disk`
  - 8301ms | `show pending changes`
  - 8286ms | `save my work to github`
  - 8210ms | `trim my disk`
  - 8208ms | `branch info`
  - 8158ms | `can you help me delete stuff`