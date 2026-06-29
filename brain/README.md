# brain

Vector memory search, context anticipation, and research aggregation.

## What It Does

- **Semantic memory search** — ChromaDB vector store + sentence-transformers (`brain/memory/vector/`)
- **Anticipation engine** — predicts next actions from behavior patterns, ranks suggestions
- **Memory curation** — Ollama-powered curator keeps MEMORY.md, DECISIONS.md, PATTERNS.md accurate and lean
- **Research engine** — idea capture, research plans, analyses, decision drafts
- **Context injection** — `brain/injector/` feeds workspace state into prompts
- **Knowledge graph** — `brain/graph/` builds and queries a cross-organ dependency graph
- **Obsidian vault** — `brain/vault/` for long-form notes and knowledge management

## Key Files

| File/Dir | Purpose |
|----------|---------|
| `brain/memory/MEMORY.md` | Durable workspace facts — single source of truth |
| `brain/memory/DECISIONS.md` | Key decisions made and their reasoning |
| `brain/memory/PATTERNS.md` | Recurring operating patterns |
| `brain/memory/INSIGHTS.md` | Higher-level learnings |
| `brain/memory/SESSION_HANDOFF.md` | Latest session summary for continuity |
| `brain/memory/memory_curator.py` | Ollama-powered memory curation (uses context_injector) |
| `brain/memory/vector/semantic_search.py` | Semantic search over workspace memory |
| `brain/anticipation/prediction_engine.py` | Predicts next likely actions |
| `brain/anticipation/prediction_memory.json` | Behavior event history |
| `brain/anticipation/action_suggestions.md` | Current ranked suggestions |
| `brain/research/` | idea-start → research-plan → analysis → decision pipeline |
| `brain/graph/build_graph.py` | Builds cross-organ knowledge graph |
| `brain/graph/graph_query.py` | Query the knowledge graph |
| `brain/system/` | System audit artifacts and gap analysis |

## CLI Commands

```bash
memory-search "query"    # Semantic vector search over workspace memory
memory-curate            # Ollama memory curation pass (uses suneelworkspace model)
memory-reindex           # Rebuild the vector index from scratch
brain-inject             # Inject context into a prompt via brain/injector/
brain-staleness          # Check for stale context entries
brain-synthesize         # Synthesize context from multiple sources
brain-graph-build        # Build the cross-organ knowledge graph
brain-graph-query "q"    # Query the knowledge graph
brain-graph-orphans      # Find orphaned nodes
idea-start               # Capture a new idea for research
idea-run                 # Run research pipeline on an idea
morning-brief-personal   # Personalized digest built from memory + goals
```

## Memory Rules

- Store only stable, useful facts in MEMORY.md
- Never store secrets, tokens, passwords, billing data, or temporary noise
- Prefer updating an existing bullet over adding duplicates
- `memory_curator.py` runs every 12h — appends insights, marks stale with `[STALE]`, never deletes

## Tests

Covered by `tests/organs/brain/test_brain.py` — part of the 103/103 passing suite.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("brain", "memory_updated", "brain/memory/MEMORY.md")
```

*Updated: 2026-06-28*
