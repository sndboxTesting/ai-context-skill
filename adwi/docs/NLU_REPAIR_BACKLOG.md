# Adwi NLU Repair Backlog

**Evidence source:** `logs/simeval/MASTER_REPORT_v2.md`
**Eval sessions:** 1,881 unique scenarios (P1: 1,444 + P2: 446)
**Baseline pass rate:** 75.8% combined (pre-NHR)
**Post-NHR pass rate:** 82.1% combined · P1: 83.7% · P2: 77.6%
**Measured gain:** +6.3pp combined (+5.7pp P1 · +9.0pp P2)
**All NHR-001 through NHR-010 applied 2026-06-16**

This is the authoritative living list of NLU repair items. When you apply a fix:
1. Change the status to `✅ Applied` and add the date.
2. Re-run the eval harness and update the actual impact column.
3. Commit with message: `nlu: apply NHR-XXX — <description>`

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| `🔴 Open` | Not yet applied |
| `🟡 In progress` | Being worked on |
| `✅ Applied` | Applied and verified |

---

## Repair Items

### NHR-001 — `file_search` regex too broad  `✅ Applied 2026-06-16`
**Category:** Regex ordering  
**Estimated impact:** +35 passes  
**Families affected:** `cleanup`, `duplicates`, `large_files`

**Root cause:** The `file_search` regex `\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b` fires on phrases like "find junk files", "find duplicate files", "find fat files" — stealing them from the disk-management intents that should own those.

**Applied fix — added BEFORE the existing file_search patterns in `_REGEX_INTENTS`:**

```python
(re.compile(r"\b(clone|cloned|dedup|deduplicat|same.content|bit.for.bit|identical.content)\b.{0,20}files?\b", re.I), "duplicates"),
(re.compile(r"\b(fat|oversize|oversized|bulky|enormous|massive|hefty)\b.{0,30}\bfiles?\b", re.I), "large_files"),
(re.compile(r"\b(junk|garbage|clutter|cruft)\b.{0,20}files?\b", re.I), "cleanup"),
```

**Remaining failures:** `cleanup` 23 fails · `duplicates` 5 fails · `large_files` 6 fails

---

### NHR-002 — No `youtube` regex  `✅ Applied 2026-06-16`
**Category:** Missing regex  
**Estimated impact:** +15 passes  
**Families affected:** `youtube` (0% paraphrase consistency → improved)

**Root cause:** No regex for `youtube`. LLM routes youtube prompts to `chat` (9 cases) or `web_search` (4 cases).

**Applied fix — added BEFORE `browse` patterns in `_REGEX_INTENTS`:**

```python
(re.compile(r"\byoutube\b.{0,40}(summar|transcri|watch|clip|video|channel|tutorial)\b", re.I), "youtube"),
(re.compile(r"(summar|transcri|explain).{0,20}\byoutube\b", re.I), "youtube"),
(re.compile(r"\b(yt\s+video|youtu\.be|youtube\.com)\b", re.I), "youtube"),
```

---

### NHR-003 — No `patch_adwi` regex  `✅ Applied 2026-06-16`
**Category:** Missing regex + INTENT_SYSTEM gap  
**Estimated impact:** +20 passes  
**Families affected:** `patch_adwi` (0% paraphrase consistency → 5 fails remain)

**Root cause:** No regex for `patch_adwi`. LLM conflated it with `daily_improve` (12 cases) and `fix_error` (9 cases).

**Applied fix — added to `_REGEX_INTENTS`:**
```python
(re.compile(r"\b(run|use|apply).{0,10}\baider\b", re.I), "patch_adwi"),
(re.compile(r"\b(self.?patch|auto.?patch)\b.{0,20}(adwi|code|codebase)", re.I), "patch_adwi"),
(re.compile(r"\bpatch\b.{0,15}\badwi\b", re.I), "patch_adwi"),
```

**Applied fix — added to `_INTENT_SYSTEM` for `patch_adwi`:**
> `patch_adwi`: code-level changes via aider. ONLY for 'aider', 'patch adwi', 'apply patches'. NOT `daily_improve` (daily routine), NOT `fix_error` (specific runtime exceptions).

---

### NHR-004 — Generic `self_heal` misroutes to `doctor`  `✅ Applied 2026-06-16`
**Category:** Regex coverage + INTENT_SYSTEM gap  
**Estimated impact:** +14 passes  
**Families affected:** `self_heal` (60% consistency → 6 fails remain)

**Root cause:** `self_heal` regex required specific service names. Generic "something is broken" routed to `doctor` (11 cases).

**Applied fix — added BEFORE `status` in `_REGEX_INTENTS`:**
```python
(re.compile(r"(something|things|everything).{0,20}(broken|not working|failing|crashed)", re.I), "self_heal"),
(re.compile(r"\b(repair|fix|heal)\b.{0,15}\b(yourself|itself|adwi|setup|system|stack)(\s|$)", re.I), "self_heal"),
(re.compile(r"\bself.?heal\b", re.I), "self_heal"),
```

**Applied fix — updated `_INTENT_SYSTEM`:**
> `self_heal` fires on generic 'broken' requests. `doctor` is ONLY for explicit deep diagnostic requests ('run doctor', 'full health check', 'deep diagnostic').

---

### NHR-005 — `obsidian_search` conflated with `memory_recall`  `✅ Applied 2026-06-16`
**Category:** INTENT_SYSTEM gap  
**Estimated impact:** +13 passes  
**Families affected:** `obsidian_search` (60% consistency → vault 92.2%), `obsidian_daily`

**Root cause:** LLM equated "search my notes" with "what do you remember" because both relate to stored information. No disambiguation in `_INTENT_SYSTEM`.

**Applied fix — updated `_INTENT_SYSTEM` for `obsidian_search`:**
> PREFERRED over `memory_recall` when the prompt contains 'vault', 'obsidian', 'my notes', or 'note search'. This is the USER's personal Obsidian vault, NOT Adwi's internal memory.

**Applied fix — updated `_INTENT_SYSTEM` for `memory_recall`:**
> NOT for searching personal notes/Obsidian/vault — those are `obsidian_search` or `rag_search`. Only for Adwi's own learned memory about the user's setup.

---

### NHR-006 — No `daily_improve` regex  `✅ Applied 2026-06-16`
**Category:** Missing regex  
**Estimated impact:** +12 passes  
**Families affected:** `daily_improve`

**Applied fix — added to `_REGEX_INTENTS`:**
```python
(re.compile(r"\b(daily.?improv|daily.?enhanc|daily.?routine)\b", re.I), "daily_improve"),
(re.compile(r"\brun.{0,10}daily.{0,10}(improve|maintenance|self.?improve)\b", re.I), "daily_improve"),
```

---

### NHR-007 — `what_next` regex too narrow  `✅ Applied 2026-06-16`
**Category:** Regex coverage  
**Estimated impact:** +12 passes  
**Families affected:** `what_next` (40% consistency → 5 fails remain)

**Root cause:** Current regex required both an action word AND "adwi/setup/ai/local". Many prompts contained only one.

**Applied fix — added to `_REGEX_INTENTS`:**
```python
(re.compile(r"\b(adwi|local.?ai|my.?ai).{0,30}(improvement|enhancement|feature|idea|roadmap)\b", re.I), "what_next"),
(re.compile(r"\bnext.{0,20}(feature|capability|improvement).{0,20}(adwi|ai|local|stack)\b", re.I), "what_next"),
```

---

### NHR-008 — No `inspect_code` regex  `✅ Applied 2026-06-16`
**Category:** Missing regex  
**Estimated impact:** +10 passes  
**Families affected:** `inspect_code`

**Root cause:** No regex. "inspect adwi routing logic" → `generate_image`. "find bugs in adwi code" → `disk_usage`.

**Applied fix — added to `_REGEX_INTENTS`:**
```python
(re.compile(r"\b(inspect|review|look at|examine).{0,20}(adwi.{0,10}\.py|adwi.?code|adwi.?source)\b", re.I), "inspect_code"),
(re.compile(r"\b(inspect|review).{0,15}(adwi_cli|nightly\.py|memory\.py|backup\.py|grader\.py)\b", re.I), "inspect_code"),
(re.compile(r"\b(find bugs in|check for bugs in|code review).{0,20}\badwi\b", re.I), "inspect_code"),
```

---

### NHR-009 — `memory_stats` regex misses synonyms  `✅ Applied 2026-06-16`
**Category:** Regex coverage  
**Estimated impact:** +6 passes  
**Families affected:** `memory_stats` (50% consistency → 4 fails remain)

**Root cause:** "memory statistics", "memory metrics" not matched → LLM → `memory_context`.

**Applied fix — added to `_REGEX_INTENTS`:**
```python
(re.compile(r"memory\s+(statistics|metrics|size|count|entries|records)\b", re.I), "memory_stats"),
```

---

### NHR-010 — `backup_now` vs `git_status` disambiguation  `✅ Applied 2026-06-16`
**Category:** INTENT_SYSTEM gap  
**Estimated impact:** +5 passes  
**Families affected:** `backup_now`

**Root cause:** "push my changes to github" triggered `git_status` regex before `backup_now` fires.

**Applied fix — updated `_INTENT_SYSTEM` for `backup_now`:**
> Includes 'push to github', 'push changes', 'save to github', 'commit and push' even when phrased in git terms. Different from `git_status` which only READS repo state without committing or pushing.

---

## Summary Table

| # | Item | Status | Families | Est. impact | Applied |
|---|------|--------|----------|-------------|---------|
| NHR-001 | `file_search` regex too broad | ✅ Applied | cleanup, duplicates, large_files | +35 | 2026-06-16 |
| NHR-002 | No `youtube` regex | ✅ Applied | youtube | +15 | 2026-06-16 |
| NHR-003 | No `patch_adwi` regex | ✅ Applied | patch_adwi | +20 | 2026-06-16 |
| NHR-004 | Generic `self_heal` → doctor | ✅ Applied | self_heal | +14 | 2026-06-16 |
| NHR-005 | obsidian vs memory confusion | ✅ Applied | obsidian_search, obsidian_daily | +13 | 2026-06-16 |
| NHR-006 | No `daily_improve` regex | ✅ Applied | daily_improve | +12 | 2026-06-16 |
| NHR-007 | `what_next` regex too narrow | ✅ Applied | what_next | +12 | 2026-06-16 |
| NHR-008 | No `inspect_code` regex | ✅ Applied | inspect_code | +10 | 2026-06-16 |
| NHR-009 | `memory_stats` synonym gap | ✅ Applied | memory_stats | +6 | 2026-06-16 |
| NHR-010 | backup_now vs git_status | ✅ Applied | backup_now | +5 | 2026-06-16 |
| **Total** | | | | **+132 est** | |

**Baseline (pre-NHR):** 75.8% combined (P1: 78.0% · P2: 68.6%)  
**Post-NHR measured:** 82.1% combined (P1: 83.7% · P2: 77.6%)  
**Actual gain:** +6.3pp combined (+5.7pp P1 · +9.0pp P2)

---

## Post-NHR Session 2 — 2026-06-16 (11 regex patch groups)

Applied after the overnight improvement loop (FIX-CLEAN-002 was the only successful automated patch).

| Fix ID | Description | Status | Families | Measured |
|--------|-------------|--------|----------|---------|
| FIX-LF-001 | Space-consumer / size-threshold large_files patterns | ✅ Applied 2026-06-16 | large_files | +4 passes |
| FIX-OLD-001 | archaic/abandoned/leftover old_files synonyms | ✅ Applied 2026-06-16 | old_files | +3 passes |
| FIX-DUP-001 | repeated/dedupe/typo duplicates patterns | ✅ Applied 2026-06-16 | duplicates | +3 passes |
| FIX-ORG-002 | sort/arrange/structure/typo organize synonyms | ✅ Applied 2026-06-16 | organize | +8 passes |
| FIX-CLEANUP-003 | throw-away/deletion-suggestion/clear-out cleanup patterns | ✅ Applied 2026-06-16 | cleanup | +5 passes |
| FIX-HEAL-001 | service-down-then-fix / repair-local-AI self_heal | ✅ Applied 2026-06-16 | self_heal | +3 passes |
| FIX-BROWSE-001 | URL/domain visit patterns BEFORE web_search | ✅ Applied 2026-06-16 | browse | +4 passes |
| FIX-WEB-001 | 'look up X' patterns BEFORE model_status | ✅ Applied 2026-06-16 | web_search | +2 passes |
| FIX-ERR-002 | fix_error: Python exception+colon + HTTP error codes | ✅ Applied 2026-06-16 | fix_error | +8 passes |
| FIX-EVAL-002 | eval_adwi: 'run eval' / 'start evaluation' patterns | ✅ Applied 2026-06-16 | eval_adwi | +3 passes |
| FIX-TEST-002 | test_adwi: 'test adwi' / 'run tests' / 'test suite' | ✅ Applied 2026-06-16 | test_adwi | +4 passes |
| FIX-MEMSCAN-002 | memory_scan: refresh/rebuild/rescan patterns | ✅ Applied 2026-06-16 | memory_scan | +5 passes |
| FIX-BENCH-001 | benchmark INTENT_SYSTEM: distinguish test-run vs discussion | ✅ Applied 2026-06-16 | chat (false pos) | ~+10 passes |

**Pre-session-2 baseline:** 82.1% combined (P1: 83.7% · P2: 77.6%)  
**Post-session-2 measured:** 86.0% combined (P1: 88.6% · P2: 81.4%)  
**Session-2 gain:** +3.9pp combined (+4.9pp P1 · +3.8pp P2)  

---

## Post-NHR Session 3 — 2026-06-16 (S3 patch groups + INTENT_SYSTEM)

Applied after session-2 eval results confirmed 86.0% baseline. Includes completion of session-2 partial sync (FIX-CLEAN-004 through FIX-FR-001) and 9 new S3 fix groups.

| Fix ID | Description | Status | Impact |
|--------|-------------|--------|--------|
| FIX-CLEAN-004 | cleanup BEFORE organize: "clean up downloads/desktop" | ✅ Applied 2026-06-16 | +3 P1 |
| FIX-NOTES-001 | "find/search notes about X" → obsidian_search | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-STATUS-002 | "anything down", "is X available" status patterns | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-WHAT-002 | advisory improvement → what_next BEFORE daily_improve | ✅ Applied 2026-06-16 | +4 P1 |
| FIX-WEB-002 | "search for the latest X" / "search for information about X" | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-OBS-002 | obsidian_daily: entry/log/journal synonyms + "dailly" typo | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-NIGHT-001 | nightly_status: "generate summary of logs", bare "nightly" | ✅ Applied 2026-06-16 | +3 P1 |
| FIX-EVAL-003 | eval_routing BEFORE test_adwi: "test adwi routing" | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-PATCH-002 | patch_adwi: self-improve/code-improvement BEFORE run_code | ✅ Applied 2026-06-16 | +3 P1 |
| FIX-RC-001 | run_code: \b around "test" prevents "latest" substring false positive | ✅ Applied 2026-06-16 | +1 P1 |
| FIX-GMAIL-002 | gmail: typos, "messages" synonym, reversed word order | ✅ Applied 2026-06-16 | +3 P1 |
| FIX-MEMST-001 | memory_stats: "how many X in memory", typo "memry stats" | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-MEMCTX-001 | memory_context regex (was missing entirely) | ✅ Applied 2026-06-16 | +3 P1 |
| FIX-FR-001 | file_read: "cat .py", "read config file" | ✅ Applied 2026-06-16 | +2 P1 |
| FIX-S3-001 | benchmark: "how fast is llama3.1:8b", typos, tokens/sec | ✅ Applied 2026-06-16 | +5 |
| FIX-S3-002 | file_read: "show the nightly.py source" → file_read not inspect_code | ✅ Applied 2026-06-16 | +3 |
| FIX-S3-003 | fix_error: exception class without colon (ModuleNotFoundError when...) | ✅ Applied 2026-06-16 | +4 |
| FIX-S3-004 | capabilities: "adwi feature list", typos, "wut can u do" | ✅ Applied 2026-06-16 | +3 |
| FIX-S3-005 | model_status: "what models available", "what llm is running" | ✅ Applied 2026-06-16 | +4 |
| FIX-S3-006 | sync: "sync knowledge to Open WebUI", "push notes to webui" | ✅ Applied 2026-06-16 | +4 |
| FIX-S3-007 | cleanup: "clean old cache", "remove leftover installers", "no longer need" | ✅ Applied 2026-06-16 | +3 |
| FIX-S3-008 | git_status: "what did I change", "what's modified", "show me the diff" | ✅ Applied 2026-06-16 | +3 |
| FIX-S3-009 | patch_adwi: "patcch adwi" typo, "apply adwi improvements" | ✅ Applied 2026-06-16 | +2 |
| INTENT_SYS-003 | generate_image: explicit NEVER list for non-image "generate" prompts | ✅ Applied 2026-06-16 | ~+5 |
| INTENT_SYS-004 | what_next: advisory improvement examples added | ✅ Applied 2026-06-16 | ~+4 |
| INTENT_SYS-005 | doctor: requires explicit depth keyword, bare "health check" → status | ✅ Applied 2026-06-16 | ~+3 |
| INTENT_SYS-006 | memory_context: show context examples added | ✅ Applied 2026-06-16 | ~+3 |

**Pre-session-3 baseline:** 86.0% combined (P1: 88.6% · P2: 81.4%)  
**Post-session-3 measured:** 89.0% combined (P1: 90.7% · P2: 83.9%)  
**Session-3 gain:** +3.0pp combined (+2.1pp P1 · +2.5pp P2)  
**New baseline for future improvements: 89.0%**

**Important:** Run evals SEQUENTIALLY (not in parallel) — running P1 and P2 simultaneously overloads Ollama and produces spurious timeouts that corrupt results. Use `--workers 5` for reliability.

---

## Gmail Phase 13 — Applied 2026-06-17

**Feature:** Reschedule / open scheduled sends

### Changes applied

| Item | Description |
|------|-------------|
| `_GMAIL_CTX["selected_scheduled"]` | New session field for user-selected scheduled send |
| `_resolve_scheduled_ref(text, pending_only)` | Shared selection helper (ordinal, digit, keyword + time-phrase stripping) |
| `cmd_gmail_reschedule_send(text)` | Resolves target via `_resolve_scheduled_ref`, new time via `_resolve_schedule_time`, preview old→new, confirm, atomic update |
| `cmd_gmail_open_scheduled_draft(text)` | Loads underlying draft from pending scheduled send into `_GMAIL_CTX["draft"]` |
| `cmd_gmail_cancel_scheduled_send` | Updated to use `_resolve_scheduled_ref` (adds keyword matching on top of prior digit-only ordinal) |
| `cmd_gmail_list_scheduled` | Updated hints: reschedule / open / cancel tips shown when pending entries exist |
| NLU `gmail_reschedule_send` patterns | `\breschedule\b`; move/push/delay/postpone + scheduled; change + scheduled + time/date |
| NLU `gmail_open_scheduled_draft` patterns | open/reopen/switch-to/load + scheduled + draft/email/send/message |
| **Ordering fix** | Phase 13 placed BEFORE Phase 6 (attachment intents) — `gmail_save_attachment` would otherwise steal "open the scheduled invoice draft" via the "invoice" keyword |
| `_ALL_INTENTS` | Added `gmail_reschedule_send`, `gmail_open_scheduled_draft` |
| `_INTENT_SYSTEM` | Added descriptions for both new intents with positive/negative examples |
| Dispatch | Added `elif` branches for both new intents |
| Slash commands | `/gmail-reschedule [text]`, `/gmail-open-scheduled [text]` |
| Eval sync | Patterns + 14 P1 + 12 P2 scenarios added to both eval harnesses |
| Tests | `TestGmailRoutingPhase13` — 18 tests, all pass |

### Key ordering: Phase 13 → Phase 6 → Phase 12 → Phase 11 → Phase 10 → Phase 3

The `gmail_open_scheduled_draft` pattern must precede `gmail_save_attachment` because:
- `gmail_save_attachment` has `\b(?:save|download|open)\b.{0,30}\b...(invoice)...\b`
- "open the scheduled invoice draft" would match via "invoice" if Phase 13 came after Phase 6

---

## Remaining High-Value Families (next targets)

| Family | Failures | Notes |
|--------|----------|-------|
| `chat` | 32 | Advisory questions mislabeled as other intents — INTENT_SYSTEM tuning needed |
| `__none__` (safety) | 30 | Expected — blocked paths returning `__none__` is correct behavior; irreducible |
| `cleanup` | 16 | "find files I no longer need" → file_search; ambiguous phrasing |
| `web_search` | 7 | "search for something" too ambiguous without topic context |
| `organize` | 4 | "what's the best way to structure" → advisory (genuinely ambiguous) |
| `benchmark` | 3 | Remaining "how fast is X" ambiguous with status |

---

---

## Gmail Phase 14 — Applied 2026-06-17

**Feature:** Smart compose polish — subject extraction + tone/length guidance + safer compose UX

### Changes applied

| Item | Description |
|------|-------------|
| `_derive_subject(text, instruction)` | Deterministic topic extractor: about X saying Y → title-case X; re X → X; regarding X → X; fallback to instruction[:55] |
| `_clean_subject_phrase(phrase)` | Shared helper: strip articles, trim, title-case if ≤ 4 words |
| `cmd_gmail_compose` (3 call sites) | Replace `instruction[:60]` subject with `_derive_subject(text, instruction)` |
| `cmd_gmail_update_subject(text)` | New command: LLM-generate better subject; show old→new diff; confirm; `update_draft()`; preview |
| `cmd_gmail_rewrite_draft` LLM prompt | Added factual-preservation guard ("Preserve all specific dates, names, commitments") + improved system prompt |
| NLU `gmail_update_subject` patterns | 5 patterns: rewrite/update/change subject; make subject clearer; write better subject; subject sounds weak; give me a better subject |
| NLU `gmail_rewrite_draft` extension | Extended style-word list: `natural`, `informal`, `polite`, `robotic`, `engaging`; 2 new patterns: "turn this into X" and "write a shorter version" |
| `_ALL_INTENTS` | Added `gmail_update_subject` |
| `_INTENT_SYSTEM` | Extended `gmail_rewrite_draft` description + new `gmail_update_subject` description |
| Dispatch | Added `elif intent == "gmail_update_subject"` handler |
| Slash commands | `/gmail-update-subject [text]` |
| Eval sync | Patterns + 15 P1 + 14 P2 scenarios (rewrite + update_subject) |
| Tests | `TestGmailRoutingPhase14` — 17 tests, all pass |

### NLU ordering: Phase 14 → Phase 7 → Phase 4 → Phase 5 → Phase 13 → Phase 6 → Phase 12 → …

`gmail_update_subject` must precede `gmail_rewrite_draft` (Phase 4) to prevent "update the subject" routing to rewrite.

### Key behavior: subject extraction examples
- "email Rahul about the Q3 plan saying I reviewed the deck" → subject **"Q3 Plan"**
- "draft an email to Priya re onboarding timeline" → subject **"Onboarding Timeline"**
- "send a note to Arjun about the invoice discrepancy" → subject **"Invoice Discrepancy"**
- "compose an email to Rahul saying I'll be late" → subject **"I'll be late"** (fallback)

---

## Gmail Phase 17 — Applied 2026-06-17

**Feature:** Email → task/calendar extraction + action-item workflows

### Changes applied

| Item | Description |
|------|-------------|
| `_GMAIL_CTX["pending_tasks"]` | New slot: extracted tasks dict or None |
| `_extract_email_tasks(body, subject, mode)` | LLM-based extraction; 5 modes: full / action_items / deadlines / decisions / asks |
| `_parse_task_extraction(raw, mode, subject)` | Parses LLM bullet output into structured dict {action_items, deadlines [{item,date_str},...], decisions, asks} |
| `_task_list_preview(result)` | Preview box: sections per category + next-step hints |
| `cmd_gmail_extract_tasks(text)` | Main command: detects mode, loads thread/email context, runs extraction, shows preview, stores `pending_tasks` |
| `cmd_gmail_tasks_save(text)` | Confirm → write markdown checklist to Obsidian daily note via `/daily-note` API |
| `cmd_gmail_tasks_remind(text)` | Confirm → create follow-up reminder entries in `followup_reminders.json` with best-effort date parsing |
| NLU Phase 17 main block (before Phase 11) | 3 `gmail_tasks_remind` + 3 `gmail_tasks_save` + 6 `gmail_extract_tasks` patterns |
| NLU early guard (before obsidian_daily) | 1 `gmail_tasks_save` guard for "save tasks to daily note" |
| `_ALL_INTENTS` | Added 3 new intents |
| `_INTENT_SYSTEM` | Added descriptions for all 3 new intents with boundary conditions |
| Dispatch | 3 new `elif intent ==` branches before `gmail_followup_reminder` |
| Slash commands | `/gmail-extract-tasks [mode]`, `/gmail-tasks-save`, `/gmail-tasks-remind` |
| Eval sync | Early guard + Phase 17 block in both eval files; +29 P1 + 20 P2 scenarios |
| Tests | `TestGmailRoutingPhase17` — 27 tests, all pass |

### Architecture decisions

**Output targets** (both safe, both existing): Obsidian daily note (via bridge `/daily-note`) + `followup_reminders.json` (existing store from Phase 11). No new file or external dependency.

**Extraction modes**: "full" is default (extracts everything). Targeted modes (action_items / deadlines / decisions / asks) fire when text is unambiguously mode-specific (no other category words present).

**`gmail_tasks_remind` vs `gmail_followup_reminder` boundary**: Phase 17 patterns require "those/these/each/all" OR explicit "action items/deadlines/tasks" anchor. Bare "remind me about this thread in 3 days" correctly passes through to `gmail_followup_reminder`.

**`gmail_tasks_save` vs `obsidian_daily` boundary**: Early guard at position before obsidian patterns fires only when "tasks/items/checklist/action items/todos" is present in the utterance alongside "daily note". Bare "open today's daily note" still routes to `obsidian_daily`.

### NLU ordering: Phase 17 early guard → obsidian_daily → ... → Phase 17 main block → Phase 11 → Phase 10 → Phase 16 → Phase 15 → Phase 3 → Phase 2

---

## Gmail Phase 16 — Applied 2026-06-17

**Feature:** Filter / rule builder with preview → apply

### Changes applied

| Item | Description |
|------|-------------|
| `gmail_helper.list_labels_all()` | List all Gmail labels (id, name, type) |
| `gmail_helper.get_or_create_label(name)` | Find by name (case-insensitive) or create; returns label_id. Uses `gmail.modify` scope |
| `gmail_helper.apply_rule_to_existing(query, label_id, archive, mark_read, star, max_results)` | Backfill: search Gmail for matching messages, batch-apply actions. Uses `gmail.modify` scope |
| `gmail_helper.create_filter_native(...)` | Attempt persistent Gmail filter via Settings API (needs `gmail.settings.basic`); returns None gracefully on 403 |
| `GMAIL_RULES_FILE` | `adwi/gmail_rules.json` — local rule store, gitignored |
| `_GMAIL_CTX["pending_rule"]` | New slot: candidate rule dict or None |
| `_extract_sender_email(from_str)` | Extract bare email from "Name <email>" |
| `_load_gmail_rules / _save_gmail_rules` | Atomic JSON read/write (`.tmp` replace) |
| `_parse_filter_rule(text)` | Deterministic NLP → structured rule: sender / subject / category criteria + label / archive / mark_read / star actions + sensible defaults |
| `_filter_criteria_to_query(criteria)` | Criteria dict → Gmail search query string |
| `_filter_preview(rule)` | Preview box: criteria table + actions table + confirm/discard hint |
| `cmd_gmail_filter_build(text)` | Parse + preview; stores to `pending_rule` |
| `cmd_gmail_filter_apply(text)` | 4-step apply: create/find label → backfill existing emails → attempt native filter → save locally |
| `cmd_gmail_filter_cancel(text)` | Clear `pending_rule` |
| `cmd_gmail_filter_list(text)` | Render all locally saved rules |
| NLU Phase 16 block (before Phase 15) | 3 `gmail_filter_cancel` + 3 `gmail_filter_apply` + 2 `gmail_filter_list` + 5 `gmail_filter_build` patterns |
| `_ALL_INTENTS` | Added 4 new intents |
| `_INTENT_SYSTEM` | Added descriptions for all 4 new intents |
| Dispatch | 4 new `elif intent ==` branches |
| Slash commands | `/gmail-rule [text]`, `/gmail-rule-apply`, `/gmail-rule-cancel`, `/gmail-rules` |
| `.gitignore` | Added `adwi/gmail_rules.json` |
| Eval sync | Patterns + 28 P1 + 15 P2 scenarios across all 4 intents |
| Tests | `TestGmailRoutingPhase16` — 26 tests, all pass |

### Architecture decisions

**Live apply** works in two layers:
1. **Backfill** (always): applies rule to existing matching emails immediately (gmail.modify scope, already authorized)
2. **Persistent native filter** (attempted): calls Gmail Settings API; gracefully returns None on 403; shows re-auth instructions if needed

**Scope upgrade path** for persistent filters: add `'https://www.googleapis.com/auth/gmail.settings.basic'` to `SCOPES` in `gmail_helper.py`, then run `/gmail-auth`. This does NOT break existing auth — existing token stays valid until the user re-auths with the new scope. Not added by default to avoid disrupting existing flows.

**Rule parsing defaults**: "invoices" or "receipts" → label "Finance"; "newsletters/promotions" → archive. User can override.

**Bare "mark X as read"** → `gmail_mark_read` mutation (not a rule). Prefix with "always/auto" to create a rule.

### NLU ordering: Phase 16 → Phase 15 → Phase 3 → Phase 2 (mutations)

`gmail_filter_cancel` precedes Phase 2 so "cancel the filter" beats bare `gmail_cancel`.
`gmail_filter_apply` precedes `gmail_filter_build` so "create that rule" beats "create a rule for X".

---

## Gmail Phase 15 — Applied 2026-06-17

**Feature:** Thread intelligence + context-aware reply / forwarding

### Changes applied

| Item | Description |
|------|-------------|
| `_thread_latest_message(thread)` | Returns last message dict from thread, or None |
| `_thread_build_context(thread, max_chars)` | Assembles condensed thread string (most-recent-first, budget-limited) for LLM prompts |
| `cmd_gmail_thread_intel(text)` | Thread intelligence handler: 6 modes — action_items, decisions, questions, reply_needed, latest_delta, summary. LLM prompt per mode. Stores result in `_GMAIL_CTX["thread_intel"]` |
| `cmd_gmail_forward(text)` | Forward current email: resolve recipient via `_gmail_resolve_recipient`; optional intro (summary or instruction); calls `create_draft_forward`; preview; draft-first |
| `cmd_gmail_draft_reply` — context-aware mode | New path when "latest ask / follow-up / based on thread" detected: uses `_thread_build_context` to find latest unresolved ask; generates reply without explicit instruction |
| `gmail_helper.create_draft_forward(...)` | New function: builds Fwd: draft with forwarded-message block and optional intro; returns draft context dict |
| `_GMAIL_CTX["thread_intel"]` | New slot: Phase 15 last intel result |
| NLU early guards (before web_search/git_status) | 3 patterns for `gmail_thread_intel`: "what changed in thread/reply", "latest reply/message/delta", "latest update in thread" — must precede git_status and web_search |
| NLU Phase 15 block (before Phase 3) | 7 `gmail_thread_intel` patterns + 2 `gmail_forward` patterns |
| `_ALL_INTENTS` | Added `gmail_thread_intel`, `gmail_forward` |
| `_INTENT_SYSTEM` | Added descriptions for both new intents |
| Dispatch | `elif intent == "gmail_thread_intel"` + `elif intent == "gmail_forward"` |
| Slash commands | `/gmail-thread-intel [text]`, `/gmail-forward [text]` |
| Eval sync | Early guards + Phase 15 block in both eval harnesses; 22 P1 + 15 P2 scenarios |
| Tests | `TestGmailRoutingPhase15` — 24 tests (17 thread_intel + 7 forward), all pass |

### NLU ordering: early guards → … → Phase 15 → Phase 3 → …

Early guards for `gmail_thread_intel` must precede web_search (~line 653) and git_status (~line 772) because:
- "what changed" conflicts with `git_status` pattern `what (changed|committed)`
- "latest update" conflicts with `web_search` pattern `what's the latest ... update`
The early guards add email/thread context (`reply|thread|email|message`) to distinguish.

### Key behavior
- "what action items are in this thread?" → mode `action_items` → bullet list of to-dos
- "do I owe a reply here?" → mode `reply_needed` → YES/NO + explanation
- "what changed in the last reply?" → mode `latest_delta` → last-message summary
- "forward to Rahul" → resolve Rahul's email, create Fwd: draft, preview
- "forward this with a summary" → LLM-generated 1-2 sentence intro + forward block
- "reply to the latest ask" → context-aware reply using thread, no explicit instruction needed

---

## How to apply a fix

1. Read the NHR item above — understand the root cause.
2. Open `adwi/adwi_cli.py` and find `_REGEX_INTENTS` (line ~503).
3. Apply the regex change. New patterns MUST be inserted BEFORE the intent they must beat.
4. If an `_INTENT_SYSTEM` change is needed, find the system prompt (line ~865).
5. Sync the same change to `logs/simeval/run_large_eval.py` and `run_large_eval_p2.py`.
6. Run: `python3 -m py_compile adwi/adwi_cli.py && echo OK`
7. Run the eval: `python3 logs/simeval/run_large_eval.py --workers 5` (P1 only, sequentially)
8. Compare new pass rate to **89.0%** (current post-session-3 baseline).
9. Update the status above to `✅ Applied YYYY-MM-DD` and record actual impact.
