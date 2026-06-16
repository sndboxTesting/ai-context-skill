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

## Remaining High-Value Families (next targets)

| Family | Failures | Notes |
|--------|----------|-------|
| `chat` | 76 | LLM-level disambiguation (benchmark, status, memory_recall bleed) |
| `__none__` (safety) | 30 | Expected — blocked paths returning `__none__` is correct |
| `cleanup` | 23 | Broader synonym coverage needed |
| `organize` | 14 | New intent or map to file_search |
| `fix_error` | 12 | Pasted tracebacks vs status vs patch_adwi edge cases |
| `web_search` | 11 | Regex tightening for "look up" vs model_status |
| `eval` | 17 | eval_adwi, eval_routing, test_adwi share similar surface area |

---

## How to apply a fix

1. Read the NHR item above — understand the root cause.
2. Open `adwi/adwi_cli.py` and find `_REGEX_INTENTS` (line ~503).
3. Apply the regex change. New patterns MUST be inserted BEFORE the intent they must beat.
4. If an `_INTENT_SYSTEM` change is needed, find the system prompt (line ~865).
5. Run: `python3 -m py_compile adwi/adwi_cli.py && echo OK`
6. Run the eval: `python3 logs/simeval/run_large_eval.py --workers 5`
7. Compare new pass rate to 82.1% (current post-NHR baseline).
8. Update the status above to `✅ Applied YYYY-MM-DD` and record actual impact.
9. Also run SimLab golden baseline: `python3 -m adwi.simlab` to confirm no regression.
