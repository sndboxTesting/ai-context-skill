---
type: map-of-content
status: active
tags: [eval, nlu, reliability, simlab]
updated: 2026-06-21
---

# Eval and Reliability Map

How Adwi measures and improves its own NLU accuracy.

## Current Baseline (2026-06-20)

| Eval | Scenarios | Pass rate | Safety breaches |
|------|-----------|-----------|-----------------|
| Large P1 (broad) | 1,834 | **98.4%** | 0 |
| Large P2 (weak families) | 570 | **98.2%** | 0 |
| Combined (dedup) | 2,283 | **98.3%** | 0 |

Regex fast-path handles 67.8% of queries. Stop Condition B (>98% combined) reached 2026-06-19.

## Three Eval Layers

| Layer | File | Tests | Speed |
|-------|------|-------|-------|
| Fast regex unit tests | `adwi/simlab/tests/test_nlu_regex.py` | 481 | ~0.1s, no Ollama |
| Large eval P1 | `adwi/logs/simeval/run_large_eval.py` | 1,834 | ~30 min |
| Large eval P2 | `adwi/logs/simeval/run_large_eval_p2.py` | 570 | ~10 min |

## SimLab (Bounded Continuous Eval)

- Runs nightly at 2 AM via LaunchAgent
- Hardware gates: battery off AC → hard block; load > 75% → pause
- Improvement tiers: **A** (add fixtures, auto), **B** (regex, after golden check), **C** (safety — human only)
- Golden baseline: `adwi/simlab/golden_baseline.jsonl` — 20 immutable scenarios, 100% required
- Rollback: `git checkout HEAD -- <file>` if golden regression

## Running Evals

```bash
# Fast regression (no Ollama needed)
python3 -m unittest adwi/simlab/tests/test_nlu_regex.py   # 481 tests, ~5s

# Full evals (run SEQUENTIALLY — parallel causes 50-70 Ollama timeouts)
python3 adwi/logs/simeval/run_large_eval.py --workers 3
python3 adwi/logs/simeval/run_large_eval_p2.py --workers 3

# Combined report
python3 adwi/logs/simeval/generate_master_report.py \
    adwi/logs/simeval/<p1-dir> adwi/logs/simeval/<p2-dir>
```

## Remaining Failures (P1: 24, P2: 4)

| Family | Count | Why |
|--------|-------|-----|
| `disk_usage` → `__none__` | 10 | LLM misroute under load — regex handles 70% |
| `chat` advisory mislabeling | 5 | LLM variance — no regex fix practical |
| Single-intent LLM variance | 9 | 1 each across various intents |
| P2 LLM variance | 4 | chat/search phrase variants |

## Key Invariants

1. `_REGEX_INTENTS` ordering is load-bearing — first match wins
2. SimLab Tier C (safety changes) — human review only, never auto-applied
3. Golden baseline 100% required before any Tier B promotion
4. P1 and P2 evals must run sequentially (never parallel)

## Related Notes

- [[projects/Adwi]]
- [[knowledge/System Map]]
- [MASTER_REPORT_v2.md](../../adwi/logs/simeval/MASTER_REPORT_v2.md)
- [NLU_REPAIR_BACKLOG.md](../../adwi/docs/NLU_REPAIR_BACKLOG.md)

## Next Improvements

- [ ] Resolve 1 open NHR item in NLU_REPAIR_BACKLOG.md
- [ ] Fix 10 `disk_usage` failures (LLM-side, not regex — may need INTENT_SYSTEM hint)
- [ ] Add Telegram bridge intents to eval harnesses
