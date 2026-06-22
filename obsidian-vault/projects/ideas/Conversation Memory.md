---
type: idea
status: planned
tags: [idea, roadmap, memory, context]
updated: 2026-06-21
---

# Conversation Memory

#idea #roadmap #memory

## Status
🔵 Planned — not started

## Why It Matters
Each Adwi REPL session starts cold — no memory of what was discussed yesterday. Persisting multi-turn chat history across sessions would let Adwi recall previous decisions, ongoing projects, and user preferences without re-explaining every time.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/memory.py` | AdwiMemory class — SQLite + cosine search |
| `adwi/adwi_cli.py` | `CHAT_HISTORY` list — in-process only, lost on exit |
| `adwi/adwi_cli.py` | `/memory-recall`, `/memory-scan`, `/memory-curate` |
| `adwi/notes/adwi-learning-journal.md` | Manual learning journal |
| `adwi/overnight_learn.py` | Indexes workspace docs — not conversation history |

## Implementation Sketch

1. On each REPL exit, serialize `CHAT_HISTORY` to a JSON file in `adwi/notes/sessions/YYYY-MM-DD-HH.json`
2. On startup, use `/memory-recall` to inject the 3 most relevant past exchanges into the system prompt
3. Add `AdwiMemory.ingest_session()` to parse session JSON and embed key exchanges
4. Surface via `/memory-context` — show what session context would be injected
5. Add `memory-curate` step to nightly loop: review last session, promote durable items

Key design choice: don't inject all history (context bloat) — use semantic retrieval to inject only relevant past exchanges.

## Risks

- Context bloat: injecting too much history degrades quality and costs tokens
- Privacy: session logs contain personal data — must stay gitignored
- Stale context: old decisions may be wrong now — need timestamps and expiry
- CHAT_HISTORY may not have clean enough signal to be useful without curation

## Next Action

Add session serialization to the REPL exit handler. Start logging. After one week of sessions, evaluate quality before adding retrieval injection.

## Related Notes

- [[knowledge/Memory and Knowledge Map]]
- [[projects/ideas/Mistake Pattern Detection]]
- [[knowledge/Ideas Index]]
- [adwi/memory.py](../../../adwi/memory.py)
