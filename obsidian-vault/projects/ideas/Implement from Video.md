---
type: idea
status: planned
tags: [idea, roadmap, video, implementation]
updated: 2026-06-21
---

# Implement-from-Video Flow

#idea #roadmap #video

## Status
🔵 Planned — not started

## Why It Matters
You can paste a YouTube tutorial URL and say "implement this" — Adwi transcribes the video, extracts the implementation steps, builds a plan, and applies it. Eliminates the copy-paste loop when following a tutorial.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/adwi_cli.py` | `/youtube <url>` already summarizes via transcript |
| `adwi/adwi_cli.py` | `/save-youtube <url>` saves summary to notes |
| `adwi/adwi_cli.py` | `/implement-idea [src]` drafts implementation |
| `adwi/reason_engine.py` | LangGraph executor for the implementation step |
| `adwi/voice.py` | STT pipeline (could transcribe audio track) |

## Implementation Sketch

1. Detect YouTube URL in user message → route to new `implement_from_video` handler
2. Call `/youtube` pipeline to get transcript + summary
3. Extract ordered implementation steps from transcript via adwi:latest
4. Build a LangGraph plan from the steps
5. Run through `/reason` with user confirmation at each step
6. Save to `adwi/notes/research/<title>.md`

## Risks

- Long videos: transcripts can be 50K+ tokens — may exceed context window; chunk or summarize first
- Code quality: tutorial code may not match your stack — needs review gate before applying
- Copyright: transcript is fair use for personal use; don't store/share full transcripts

## Next Action

Test `/youtube <url>` on a 10-minute coding tutorial and check if the output is detailed enough to feed into `/implement-idea`.

## Related Notes

- [[projects/ideas/Article URL Implementation Flow]]
- [[projects/ideas/Multi-Agent Execution]]
- [[knowledge/Ideas Index]]
