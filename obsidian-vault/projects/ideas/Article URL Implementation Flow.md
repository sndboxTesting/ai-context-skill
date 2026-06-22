---
type: idea
status: planned
tags: [idea, roadmap, url, implementation]
updated: 2026-06-21
---

# Article / URL Implementation Flow

#idea #roadmap #url

## Status
🔵 Planned — not started

## Why It Matters
Paste a blog post, GitHub README, or documentation URL and say "implement this" — Adwi fetches the page, extracts actionable steps, and builds a plan. Reduces friction when following written guides.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/adwi_cli.py` | `/browse <url>` fetches + summarizes pages |
| `adwi/adwi_cli.py` | `/url <url>` summarizes a webpage |
| `adwi/adwi_cli.py` | `/extract-ideas [src]` extracts implementable ideas |
| `adwi/adwi_cli.py` | `/implement-idea [src]` drafts + implements an idea |
| `adwi/adwi_cli.py` | `/firecrawl <url>` → clean markdown via Firecrawl API |
| `adwi/reason_engine.py` | Executor for the implementation steps |

## Implementation Sketch

1. User pastes URL + "implement this" → NLU routes to `implement_from_url`
2. Fetch via `/browse` chain (Firecrawl → Jina → Playwright → urllib)
3. Extract ordered steps via adwi:latest
4. Build LangGraph plan
5. Run through `/reason` with confirmation gates
6. Save extraction to `notes/research/<title>.md`

Simple case: this is mostly wiring `/browse` → `/extract-ideas` → `/implement-idea` together with a single user intent.

## Risks

- Paywalled pages: Firecrawl/Playwright may not bypass paywalls
- Long articles: chunk if > 32K tokens
- Ambiguous instructions: LLM may misinterpret step ordering — always show plan before executing

## Next Action

Test the full chain manually: `/browse <blog-url>` → copy output → `/implement-idea` with that text. If it works, automate the handoff.

## Related Notes

- [[projects/ideas/Implement from Video]]
- [[knowledge/Automation Map]]
- [[knowledge/Ideas Index]]
