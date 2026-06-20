# Adwi Internet Search Upgrade Pack

Added 2026-06-19. This phase turns Adwi's fragmented internet search paths into
a shared orchestrator used by the CLI and reason engine.

## Current provider support

| Provider | Role | Config |
|---|---|---|
| SearXNG | Local/private baseline search | `SEARXNG_URL` optional override, defaults to `http://127.0.0.1:8888` |
| Brave Search | Optional independent web index | `BRAVE_SEARCH_API_KEY` |
| Tavily | Optional curated web search | `TAVILY_API_KEY` |
| Exa | Optional semantic/neural search | `EXA_API_KEY` |
| Firecrawl | Optional clean page markdown extraction | `FIRECRAWL_API_KEY` |
| Jina Reader | Optional extraction fallback | `JINA_API_KEY` |
| Playwright | Local JS-capable fetch fallback | Python package/runtime availability |
| urllib | Final local fetch fallback | stdlib |

Optional providers are skipped when their env var is absent or still contains a
template placeholder. Adwi does not report them as live unless the key is real.

## Shared orchestrator

Core module: `adwi/search_orchestrator.py`

It provides:

- normalized `SearchResult`, `FetchResult`, `SearchResponse`, and metric records
- provider routing for quick lookup and research use cases
- canonical URL dedupe with provider provenance
- bounded JSON cache under `adwi/cache/search/`
- include/exclude domain filters
- optional strict freshness filtering and freshness rerank boost
- deterministic local reranking using query match, provider weight, trust, freshness, and multi-provider agreement
- provider latency and approximate cost-unit tracking
- page fetch fallback: Firecrawl -> Jina Reader -> Playwright -> urllib

## Entry points now using it

- `/web-search`
- `/research`
- `/browse`
- `/exa`
- `/tavily`
- `reason_engine.py` web search executor

`/firecrawl` remains a provider-specific command and still requires
`FIRECRAWL_API_KEY`; it intentionally does not silently fall back to other fetch
providers because the command name promises Firecrawl.

## Research behavior

`/research` now:

- decomposes the user question into multiple search queries
- dedupes and reranks candidates from configured providers
- fetches up to six ranked pages for grounded evidence
- instructs the synthesis model to cite only fetched page evidence
- saves queries, fetched evidence, and ranked search context into the research note

Supported follow-up-style prefixes:

- `dig deeper <topic>`
- `verify <topic>`
- `compare sources <topic>`

These are command-prefix modes, not a full interactive multi-turn research agent.

## Validation

Deterministic tests live in `adwi/tests/test_search_orchestrator.py` and cover:

- URL canonicalization
- canonical dedupe
- provider env gating
- provider fallback and provenance
- include/exclude domain filters
- strict freshness filtering
- local reranking
- cache TTL
- fetch fallback
- research query decomposition and page fetching
- citation context grounding
- `reason_engine.py` alignment with the shared orchestrator

