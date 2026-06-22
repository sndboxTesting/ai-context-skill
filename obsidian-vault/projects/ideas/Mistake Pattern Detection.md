---
type: idea
status: planned
tags: [idea, roadmap, self-improvement, mistakes]
updated: 2026-06-21
---

# Mistake Pattern Detection

#idea #roadmap #self-improvement

## Status
🔵 Planned — not started

## Why It Matters
`adwi/notes/adwi-mistakes-and-fixes.md` grows over time but is currently read-only reference material. Analyzing it automatically could update NLU prompts, add regression tests, or flag recurring failure patterns before they become incidents.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/notes/adwi-mistakes-and-fixes.md` | Running bug/fix log — the data source |
| `adwi/adwi_cli.py` | `/mistakes` command reads this file |
| `adwi/adwi_cli.py` | `/learn-from-last-error` — single-error learning |
| `adwi/simlab/failure_store.py` | SHA-256 fingerprinted failure dedup DB |
| `adwi/nightly.py` | Could add a pattern-analysis step here |

## Implementation Sketch

1. Add `step_mistake_analysis(data)` to `nightly.py`
2. Read `adwi-mistakes-and-fixes.md` → chunk into bug entries
3. Run adwi:latest to classify into patterns (NLU error / path error / API error / etc.)
4. Surface top-3 recurring patterns in morning brief's `## Pending Approval` section
5. For NLU patterns: propose regex fixes to `NLU_REPAIR_BACKLOG.md` (Tier C — human review)

## Risks

- Auto-applying NLU fixes based on mistake analysis violates the Tier C human-review invariant — must be proposal-only
- Mistake log may not have enough signal yet — needs 50+ entries for pattern to be meaningful
- False positives: LLM may hallucinate patterns — confidence threshold required

## Next Action

Run `adwi:latest` on `adwi-mistakes-and-fixes.md` manually with prompt: "What recurring bug patterns do you see? Group by category." Evaluate quality before automating.

## Related Notes

- [[knowledge/Eval and Reliability Map]]
- [[knowledge/Pending Approval]]
- [[knowledge/Ideas Index]]
- [adwi/notes/adwi-mistakes-and-fixes.md](../../../adwi/notes/adwi-mistakes-and-fixes.md)
