# 🧠 Brain — SuneelWorkSpace Organ

## Purpose
Manages long-term memory, vector stores, intent predictions, knowledge graphs, and the research engine.

## What\s Inside
* `memory/`: Durable text-based memory logs (Memory, Decisions, Insights, Session Handoff).
* `memory/vector/`: Semantic query search tools and ChromaDB storage controllers.
* `anticipation/`: Intent analysis and sequence-based next action suggestions.
* `research/`: Lifecycle files for capturing ideas, compiling plans, doing research runs, and documenting decision records.

## Key Files
* [brain/memory/MEMORY.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/MEMORY.md): Durably saved facts list.
* [brain/memory/DECISIONS.md](file:///Users/MAC/SuneelWorkSpace/brain/memory/DECISIONS.md): Architectural decisions repository.
* [brain/memory/vector/semantic_search.py](file:///Users/MAC/SuneelWorkSpace/brain/memory/vector/semantic_search.py): Vector semantic matching module.
* [brain/anticipation/prediction_engine.py](file:///Users/MAC/SuneelWorkSpace/brain/anticipation/prediction_engine.py): Sequences analyzer suggesting next steps.
* [brain/research/research_engine.py](file:///Users/MAC/SuneelWorkSpace/brain/research/research_engine.py): Controller of idea execution lifecycle.

## Provides (to other organs)
* Memory search queries to `mouth` NL dispatcher and `eyes` dashboard.
* Context inputs via context-injectors.
* Anticipated suggestions to dashboard client.

## Needs (from other organs)
* Goal tracker parameters from `heart`.
* Command histories and event updates from `blood` and `nervous`.

## CLI Commands
* `memory-search`: Semantic search across all memory files.
* `memory-reindex`: Re-embeds markdown notes.
* `brain-inject`: Injects context before task executions.
* `brain-graph-build`: Rebuilds backlinks matrix files.
* `brain-graph-query`: Queries backlink structures.
* `brain-staleness`: Isolates stale or orphan memory notes.

## How To Add Something Here
1. Ensure new notes go to `brain/memory/` and code goes to vector/research/anticipation.
2. Link commands in `hands/bin/` as relative symlinks.
3. Update `brain/nerve.json` and propagate changes.
