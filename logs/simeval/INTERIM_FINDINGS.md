# Adwi NLU — Interim Findings (Pass 1, 1133/1444 scenarios)
Generated mid-run 2026-06-15

## Current Pass Rate: 79.9% (831/1040 done at checkpoint)
vs baseline 75.5% — **+4.4 pp improvement**

---

## Top 15 Failure Families (at 1040 scenario checkpoint)

| Rank | Intent | Failures | Primary Mis-route |
|------|--------|----------|-------------------|
| 1 | cleanup | 20 | → file_search (9), → large_files (4) |
| 2 | youtube | 15 | → chat (9), → web_search (4) |
| 3 | patch_adwi | 15 | → daily_improve (6), → fix_error (2) |
| 4 | self_heal | 14 | → doctor (11), → status (3) |
| 5 | large_files | 12 | → disk_usage (7), → file_search (5) |
| 6 | organize | 12 | → chat (7), → file_search (2) |
| 7 | what_next | 12 | → chat (7), → memory_recall (2) |
| 8 | obsidian_search | 12 | → memory_recall (10), → file_search (1) |
| 9 | web_search | 8 | → model_status (5), → memory_recall (3) |
| 10 | obsidian_daily | 8 | → memory_recall (5), → file_read (2) |
| 11 | browse | 6 | → web_search (4), → chat (1) |
| 12 | test_adwi | 6 | → status (3), → chat (2) |
| 13 | duplicates | 5 | → file_search (5) |
| 14 | memory_scan | 5 | → memory_recall (3), → memory_context (1) |
| 15 | memory_stats | 5 | → memory_context (4), → memory_recall (1) |

---

## Root Cause Analysis

### RCA-001: file_search Regex Over-reach (HIGH IMPACT)
**Failures caused: ~30+ (cleanup, duplicates, large_files)**

The file_search regex `\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b`
fires on:
- "find things to delete" (cleanup) — if phrased as "find junk files"
- "find duplicate files" (duplicates) — "find" + "files" matches before intent-specific content
- "find large files" (large_files) — same issue
- "find cloned files" (duplicates) — "cloned" not in duplicates regex, so file_search wins

**Root cause**: The word "find" triggers file_search whenever "files" appears within 20 chars,
regardless of semantic intent. Disk management prompts (cleanup, duplicates, old_files) 
frequently contain "find X files" phrasing.

**Fix**: Add negative lookahead or move disk-management intents BEFORE file_search:
- Add regex guards for duplicates/cleanup BEFORE file_search
- OR tighten file_search to require file path context (extension, directory path, "in /path")

---

### RCA-002: youtube Has No Regex (MEDIUM IMPACT)
**Failures caused: ~15**

No regex pattern for youtube intent. LLM classifies youtube queries as:
- `chat` (9 cases) — treats "summarize this youtube video" as chat
- `web_search` (4 cases) — routes "youtube.com/..." to web_search

**Fix**: Add regex patterns:
```python
(re.compile(r"(youtube\.com|youtu\.be|yt video).{0,40}", re.I), "youtube"),
(re.compile(r"(summar|transcri).{0,20}(youtube|yt video|youtu\.be)", re.I), "youtube"),
(re.compile(r"(youtube|youtube video).{0,30}(summar|transcri|watch)", re.I), "youtube"),
```

---

### RCA-003: obsidian_search → memory_recall LLM Confusion (HIGH IMPACT)
**Failures caused: ~22 (obsidian_search + obsidian_daily)**

LLM routes note/vault queries to memory_recall because:
- "search my notes" semantically overlaps with "what do you remember"
- "my notes" ≈ "your memory about my setup"
- _INTENT_SYSTEM doesn't have a strong disambiguation rule

obsidian_daily → memory_recall:
- "open today's note" in LLM context sounds like "what's in your memory today"
- Obsidian_daily regex correctly catches "daily note" but misses "today's journal"

**Fix A** (intent system): Add disambiguation rule:
"obsidian_search: PREFERRED over memory_recall when 'vault', 'obsidian', or 'my notes' appear 
with a search action. memory_recall is about ADWI's internal memory of the user's setup, 
NOT the user's personal notes."

**Fix B** (obsidian_daily regex): Add journal variants:
```python
(re.compile(r"\b(today.{0,10}journal|journal.{0,10}entry|morning.{0,10}note)\b", re.I), "obsidian_daily"),
(re.compile(r"\b(daily|today.s).{0,10}(log|entry|journal)\b", re.I), "obsidian_daily"),
```

---

### RCA-004: self_heal → doctor Confusion (MEDIUM IMPACT)
**Failures caused: ~14**

"something is broken fix it" routes to `doctor` instead of `self_heal`.

Root cause: the `doctor` LLM description says "deep full-system health check" which the LLM
applies to any "broken" scenario. The `self_heal` regex only fires on specific service names
(ollama, docker, stack, service, setup) — misses generic repair requests.

**Fix**: Add self_heal patterns for generic repair:
```python
(re.compile(r"(something|things|everything).{0,20}(broken|not working|failing|crashed)", re.I), "self_heal"),
(re.compile(r"(repair|fix|heal).{0,15}(yourself|myself|adwi|setup|system)$", re.I), "self_heal"),
(re.compile(r"\b(self.?heal|auto.?repair|auto.?fix|self.?repair)\b", re.I), "self_heal"),
```

Also strengthen _INTENT_SYSTEM: "self_heal fires when user says something is broken or broken 
generically WITHOUT a specific error class. doctor is only for explicit deep health check requests."

---

### RCA-005: patch_adwi → daily_improve Confusion (MEDIUM IMPACT)
**Failures caused: ~15**

"self-improve adwi", "make adwi better" routes to `daily_improve` instead of `patch_adwi`.

Root cause: both intents are about "improving adwi" and the LLM conflates them.
`patch_adwi` = code-level changes via aider. `daily_improve` = daily improvement routine.

**Fix**: Add explicit disambiguation in _INTENT_SYSTEM:
"patch_adwi: code-level changes via aider. ONLY when user says 'aider', 'patch', 'apply patches', 
'run aider', 'self-patch'. NOT the same as running the daily improvement routine."
"daily_improve: run the daily self-improvement routine. Keywords: 'daily improve', 'daily improvement'."

Also consider updating acceptable_intents to allow patch_adwi/daily_improve as near-misses (warn not fail).

---

### RCA-006: what_next → chat Confusion (MEDIUM IMPACT)
**Failures caused: ~12**

"adwi improvement ideas", "next feature recommendation" → chat.

The what_next regex requires BOTH "next/build/improve/add/create" AND "adwi/setup/ai/local".
Many what_next prompts contain only one element:
- "adwi improvement ideas" → has "adwi" but not next/build/improve in regex format
- "next feature recommendation" → has "next" and "feature" but not adwi/setup/ai/local

**Fix**: Expand what_next regex:
```python
(re.compile(r"(suggest|recommend).{0,20}(next|improvement|feature|capability).{0,20}(adwi|ai|local|stack)", re.I), "what_next"),
(re.compile(r"\b(adwi|local.?ai).{0,20}(improvement|enhancement|feature|capability).{0,20}(idea|suggest|recommend|next)", re.I), "what_next"),
```

---

### RCA-007: large_files → file_search Overshoot (MEDIUM IMPACT)
**Failures caused: ~5**

"find large files", "find huge files" prompts get grabbed by file_search regex:
`\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b`

"find large files" = "find" + "large" + "files" → file_search fires (wrong).
The large_files regex `\b(big(gest)?|large(st)?|heavy|huge)\b.{0,30}\bfiles?\b` should fire 
BEFORE file_search. Let me verify the ordering in REGEX_INTENTS:

large_files patterns are at indices 0-2
file_search patterns are at indices 17-18

So large_files SHOULD fire first. The issue is prompts like "find large files":
- large_files regex: `\b(big(gest)?|large(st)?|heavy|huge)\b.{0,30}\bfiles?\b` — matches "large files" ✓
- BUT file_search: `\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b` — also matches!
- Since large_files is checked FIRST (index 0), it SHOULD win.

Wait — this should work. Let me check if the issue is with specific prompt phrasing:
- "find fat files" → "fat" not in large_files regex → file_search fires
- "find size hogs" → no "files?" after that → file_search doesn't fire → LLM routes to large_files? 
  Actually "size hogs on my disk" → disk_usage maybe?
- "find really big files" → "really big" → "big" matches large_files → should route to large_files ✓
- "bulk space users" → no "find" or "files" → goes to LLM → disk_usage? or large_files?
- "find oversized files" → "oversized" not in large_files regex → file_search fires!

**Fix**: Expand large_files regex:
```python
(re.compile(r"\b(fat|oversize|oversized|bulky|enormous|massive)\b.{0,30}\bfiles?\b", re.I), "large_files"),
```

---

### RCA-008: duplicates → file_search via "find" + "files" (MEDIUM IMPACT)
**Failures caused: ~5**

Prompts like "find cloned files", "find same-content files" containing "find ... files" hit
file_search before duplicates can fire, because these prompts don't contain the exact keywords
in the duplicates regex `(duplicate|identical|same file|copy|copies|redundant)`.

"cloned", "identical content", "bit-for-bit" are not in the pattern.

**Fix**: Expand duplicates regex:
```python
(re.compile(r"\b(clone|cloned|dedup|deduplicat|same.content|bit.for.bit)\b.{0,20}files?\b", re.I), "duplicates"),
```

---

### RCA-009: memory_stats → memory_context Confusion (LOW IMPACT)
**Failures caused: ~5**

"memory stats" → routes to memory_context (4 cases) instead of memory_stats.

Root cause: LLM sees "memory stats" and "memory context" as similar. The memory_stats regex
`memory (stats|status|ledger|database|db)\b` SHOULD match "memory stats". 
Check: is there an issue with the regex matching the NEXT pattern first?

Actually looking at REGEX_INTENTS, there's no memory_context pattern in the regex list.
"memory stats" → matched by `memory (stats|status|ledger|database|db)\b` → memory_stats ✓

But 4/5 failures? Maybe phrasing like "memory statistics", "memory metrics" not matching → goes to LLM → memory_context?

**Fix**: Expand memory_stats regex:
```python
(re.compile(r"memory\s+(statistics|metrics|size|count|entries|records)\b", re.I), "memory_stats"),
```

---

## Summary of Confirmed Quick Wins

| Priority | Fix | Intents Fixed | Estimated Impact |
|----------|-----|--------------|------------------|
| 1 | Add duplicates/cleanup patterns BEFORE file_search | cleanup, duplicates | ~30 scenarios |
| 2 | Add youtube regex | youtube | ~15 scenarios |
| 3 | Strengthen obsidian_search vs memory_recall in INTENT_SYSTEM | obsidian_search/daily | ~22 scenarios |
| 4 | Add generic self_heal patterns | self_heal | ~11 scenarios |
| 5 | Expand what_next regex | what_next | ~12 scenarios |
| 6 | Add more large_files patterns (fat, oversized) | large_files | ~5 scenarios |
| 7 | Expand duplicates regex (cloned, dedup, bit-for-bit) | duplicates | ~5 scenarios |
| 8 | Add patch_adwi vs daily_improve disambiguation | patch_adwi | ~9 scenarios |
| 9 | Expand obsidian_daily regex (journal variants) | obsidian_daily | ~5 scenarios |
| 10 | Benchmark regex expansion (throughput, inference) | benchmark | ~15 scenarios |

**Estimated total improvement if all 10 applied: ~129 additional passes**
**Projected new pass rate: (831 + ~100 fixes) / 1040 ≈ 89%+** (on current corpus)

---

## Safety Assessment
- No safety breaches detected in 1040 scenarios tested so far
- All blocked-path probes (SSH keys, AWS creds, /etc/passwd) correctly refused or routed to chat
- Injection attempts not breaking routing to dangerous intents
