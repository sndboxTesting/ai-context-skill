---
type: map-of-content
status: active
tags: [memory, knowledge, rag, qdrant]
updated: 2026-06-21
---

# Memory and Knowledge Map

How Adwi stores, searches, and retrieves information.

## Three-Layer Memory

| Layer | Store | What lives there | Search method |
|-------|-------|-----------------|---------------|
| 1 | `adwi/memory.db` (SQLite) | Terminal history, git log, notes — importance-scored, recency-decayed | Cosine similarity via nomic-embed-text (768-dim) |
| 2 | `adwi/knowledge.db` (SQLite) | Q&A pairs, chunked docs (1,565+ entries) | Vector search + full-text |
| 3 | `obsidian-vault/` | Structured markdown notes, daily notes, ideas | Full-text search via bridge + `/obsidian-search` |

## NLU Fixtures (Qdrant)

- Collection: `nlu_fixtures`
- 96 seed fixtures, 768-dim cosine
- Threshold: `score_threshold=0.5`
- Top-3 injected into llama3.1:8b system prompt at classification time
- Bypass: Qdrant ≥0.88 score skips LLM entirely (`nlu_fast_path.py`, ~5 ms vs 43 ms)

## Key Commands

```bash
/memory-recall <query>   # 3-layer: SQLite → knowledge.db → vault full-text
/memory-scan             # re-index terminal history + git log + notes
/memory-stats            # record counts by source
/memory-context <query>  # show what would be injected into next prompt
/memory-curate           # review recent logs, propose durable memories (Y/N per item)
/rag <query>             # semantic search over notes RAG index
/rag-index               # rebuild RAG notes index
/obsidian-search <q>     # vault full-text search
```

## What Is Gitignored

- `adwi/memory.db` — contains terminal history
- `adwi/knowledge.db` — indexed workspace content
- Both regenerated per machine: `/memory-scan` (2 min) + `overnight_learn.py` (7 hr)

## Data Flow

```
Terminal history + git log + notes
    → /memory-scan
    → AdwiMemory.ingest() → nomic-embed-text
    → memory.db (SQLite, 380+ items)

Workspace docs
    → overnight_learn.py (1 AM, 7 hr)
    → knowledge.db chunks + Q&A pairs

Obsidian vault
    → obsidian-bridge :5056 (live read/write/search)
    → /obsidian-search for vault-scoped queries
```

## Related Notes

- [[knowledge/System Map]]
- [[knowledge/Eval and Reliability Map]]
- [adwi/memory.py](../../adwi/memory.py)

## Next Improvements

- [ ] Surface memory.db item counts in `/status` output
- [ ] Add vault notes to overnight_learn.py ingestion pipeline
- [ ] Expose Qdrant collection stats in `/model-status`
