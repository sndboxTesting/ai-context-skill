"""
Shared internet search orchestration for Adwi.

This module keeps search provider integration, result normalization, dedupe,
fetch fallback, caching, and deterministic reranking in one place so CLI and
reasoning flows do not drift.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ADWI_DIR = Path(__file__).resolve().parent
CONFIG_ENV = ADWI_DIR / "config" / ".env"
DEFAULT_SEARXNG_URL = "http://127.0.0.1:8888"
CACHE_VERSION = 1

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "ref",
    "ref_src",
}

SOURCE_WEIGHTS = {
    "exa": 0.72,
    "tavily": 0.70,
    "brave": 0.64,
    "searxng": 0.56,
}


def load_config_env(env_path: Path | None = None) -> None:
    """Load adwi/config/.env into os.environ without overwriting live env."""
    path = env_path or CONFIG_ENV
    if not path.exists():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value:
                os.environ.setdefault(key, value)
    except Exception:
        return


def configured_value(value: str | None) -> bool:
    """Return True only for a value that looks like a real configured secret."""
    if not value:
        return False
    value = value.strip()
    if not value:
        return False
    bad_markers = ("REPLACE_ME", "CHANGE_ME", "YOUR_", "<", ">")
    return not any(marker in value.upper() for marker in bad_markers)


def provider_status(env: dict[str, str] | None = None) -> dict[str, bool]:
    env = env or os.environ
    return {
        "searxng": bool(env.get("SEARXNG_URL", DEFAULT_SEARXNG_URL)),
        "tavily": configured_value(env.get("TAVILY_API_KEY")),
        "exa": configured_value(env.get("EXA_API_KEY")),
        "firecrawl": configured_value(env.get("FIRECRAWL_API_KEY")),
        "brave": configured_value(env.get("BRAVE_SEARCH_API_KEY")),
        "jina": configured_value(env.get("JINA_API_KEY")),
    }


def canonicalize_url(url: str) -> str:
    """Canonical URL used for dedupe, without fragments or tracking params."""
    if not url:
        return ""
    raw = url.strip()
    if not raw:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw

    try:
        parsed = urllib.parse.urlsplit(raw)
    except Exception:
        return raw.lower()

    scheme = (parsed.scheme or "https").lower()
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    port = parsed.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")

    kept_params: list[tuple[str, str]] = []
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() in TRACKING_PARAMS or key.lower().startswith("utm_"):
            continue
        kept_params.append((key, value))
    query = urllib.parse.urlencode(sorted(kept_params), doseq=True)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def result_domain(url: str) -> str:
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def domain_matches(domain: str, patterns: tuple[str, ...]) -> bool:
    domain = domain.lower().removeprefix("www.")
    for pattern in patterns:
        p = pattern.lower().strip().removeprefix("www.")
        if not p:
            continue
        if domain == p or domain.endswith("." + p):
            return True
    return False


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def query_terms(query: str) -> set[str]:
    stop = {
        "the", "and", "for", "with", "about", "into", "from", "what", "when",
        "where", "this", "that", "latest", "current", "recent", "best", "how",
        "why", "does", "are", "was", "were", "will", "would", "could",
    }
    return {t for t in re.findall(r"[a-z0-9][a-z0-9.+_-]{1,}", query.lower()) if t not in stop}


def trust_score(url: str) -> float:
    domain = result_domain(url)
    if not domain:
        return 0.35
    score = 0.50
    if domain.endswith(".gov") or domain.endswith(".edu"):
        score += 0.25
    if domain in {"github.com", "docs.github.com", "developer.mozilla.org"}:
        score += 0.18
    if domain.startswith("docs.") or ".docs." in domain:
        score += 0.16
    if domain in {"arxiv.org", "pubmed.ncbi.nlm.nih.gov", "nist.gov"}:
        score += 0.15
    if domain in {"medium.com", "reddit.com", "news.ycombinator.com"}:
        score -= 0.08
    return max(0.0, min(score, 1.0))


@dataclass
class SearchOptions:
    max_results: int = 8
    mode: str = "web"
    providers: tuple[str, ...] = ()
    include_domains: tuple[str, ...] = ()
    exclude_domains: tuple[str, ...] = ()
    freshness_days: int | None = None
    strict_freshness: bool = False
    fetch_pages: bool = False
    fetch_limit: int = 0
    use_cache: bool = True
    ttl_seconds: int = 1800

    def cache_payload(self, selected_providers: tuple[str, ...]) -> dict[str, Any]:
        return {
            "v": CACHE_VERSION,
            "max_results": self.max_results,
            "mode": self.mode,
            "providers": selected_providers,
            "include_domains": self.include_domains,
            "exclude_domains": self.exclude_domains,
            "freshness_days": self.freshness_days,
            "strict_freshness": self.strict_freshness,
            "fetch_pages": self.fetch_pages,
            "fetch_limit": self.fetch_limit,
        }


@dataclass
class FetchOptions:
    max_chars: int = 8000
    providers: tuple[str, ...] = ()
    use_cache: bool = True
    ttl_seconds: int = 86400
    allow_browser: bool = True


@dataclass
class ProviderCall:
    provider: str
    operation: str
    ok: bool
    latency_ms: int
    result_count: int = 0
    cached: bool = False
    approx_cost_units: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "ok": self.ok,
            "latency_ms": self.latency_ms,
            "result_count": self.result_count,
            "cached": self.cached,
            "approx_cost_units": self.approx_cost_units,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderCall":
        return cls(
            provider=data.get("provider", ""),
            operation=data.get("operation", ""),
            ok=bool(data.get("ok")),
            latency_ms=int(data.get("latency_ms", 0)),
            result_count=int(data.get("result_count", 0)),
            cached=bool(data.get("cached", False)),
            approx_cost_units=float(data.get("approx_cost_units", 0.0)),
            error=data.get("error", ""),
        )


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    query: str = ""
    canonical_url: str = ""
    published_date: str = ""
    score: float = 0.0
    trust: float = 0.0
    fetched_text: str = ""
    fetch_source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.canonical_url:
            self.canonical_url = canonicalize_url(self.url)
        if not self.trust:
            self.trust = trust_score(self.url)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "query": self.query,
            "canonical_url": self.canonical_url,
            "published_date": self.published_date,
            "score": self.score,
            "trust": self.trust,
            "fetched_text": self.fetched_text,
            "fetch_source": self.fetch_source,
            "metadata": self.metadata,
        }

    def to_legacy_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.snippet,
            "source": self.source,
            "published_date": self.published_date,
            "score": self.score,
            "trust": self.trust,
            "fetched_text": self.fetched_text,
            "fetch_source": self.fetch_source,
            "providers": self.metadata.get("providers", [self.source] if self.source else []),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResult":
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            snippet=data.get("snippet", ""),
            source=data.get("source", ""),
            query=data.get("query", ""),
            canonical_url=data.get("canonical_url", ""),
            published_date=data.get("published_date", ""),
            score=float(data.get("score", 0.0)),
            trust=float(data.get("trust", 0.0)),
            fetched_text=data.get("fetched_text", ""),
            fetch_source=data.get("fetch_source", ""),
            metadata=data.get("metadata", {}) or {},
        )


@dataclass
class FetchResult:
    url: str
    title: str = ""
    text: str = ""
    source: str = ""
    success: bool = False
    error: str = ""
    canonical_url: str = ""
    latency_ms: int = 0
    cached: bool = False

    def __post_init__(self) -> None:
        if not self.canonical_url:
            self.canonical_url = canonicalize_url(self.url)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text,
            "source": self.source,
            "success": self.success,
            "error": self.error,
            "canonical_url": self.canonical_url,
            "latency_ms": self.latency_ms,
            "cached": self.cached,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FetchResult":
        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            text=data.get("text", ""),
            source=data.get("source", ""),
            success=bool(data.get("success", False)),
            error=data.get("error", ""),
            canonical_url=data.get("canonical_url", ""),
            latency_ms=int(data.get("latency_ms", 0)),
            cached=bool(data.get("cached", False)),
        )


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    sources: list[str] = field(default_factory=list)
    metrics: list[ProviderCall] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    elapsed_ms: int = 0
    cache_hit: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "sources": self.sources,
            "metrics": [m.to_dict() for m in self.metrics],
            "warnings": self.warnings,
            "elapsed_ms": self.elapsed_ms,
            "cache_hit": self.cache_hit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SearchResponse":
        return cls(
            query=data.get("query", ""),
            results=[SearchResult.from_dict(r) for r in data.get("results", [])],
            sources=list(data.get("sources", [])),
            metrics=[ProviderCall.from_dict(m) for m in data.get("metrics", [])],
            warnings=list(data.get("warnings", [])),
            elapsed_ms=int(data.get("elapsed_ms", 0)),
            cache_hit=bool(data.get("cache_hit", False)),
        )


@dataclass
class ResearchBundle:
    question: str
    mode: str
    queries: list[str]
    response: SearchResponse
    fetched_count: int

    @property
    def results(self) -> list[SearchResult]:
        return self.response.results


class SearchCache:
    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or (ADWI_DIR / "cache" / "search")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, namespace: str, key: dict[str, Any]) -> Path:
        raw = json.dumps(key, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{namespace}-{digest}.json"

    def get(self, namespace: str, key: dict[str, Any], ttl_seconds: int) -> dict[str, Any] | None:
        path = self._path(namespace, key)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            created = float(data.get("created", 0))
            if ttl_seconds >= 0 and time.time() - created > ttl_seconds:
                return None
            return data.get("payload")
        except Exception:
            return None

    def set(self, namespace: str, key: dict[str, Any], payload: dict[str, Any]) -> None:
        path = self._path(namespace, key)
        data = {"created": time.time(), "payload": payload}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)


class SearchOrchestrator:
    def __init__(
        self,
        env: dict[str, str] | None = None,
        cache_dir: Path | None = None,
        env_path: Path | None = None,
    ):
        load_config_env(env_path)
        self.env = dict(os.environ if env is None else env)
        self.cache = SearchCache(cache_dir)

    def configured_providers(self) -> dict[str, bool]:
        return provider_status(self.env)

    def search(self, query: str, options: SearchOptions | None = None) -> SearchResponse:
        options = options or SearchOptions()
        selected = self._select_search_providers(options)
        cache_key = {"kind": "search", "query": query, "options": options.cache_payload(selected)}

        if options.use_cache:
            cached = self.cache.get("search", cache_key, options.ttl_seconds)
            if cached:
                response = SearchResponse.from_dict(cached)
                response.cache_hit = True
                response.metrics.append(ProviderCall("orchestrator", "search_cache", True, 0, len(response.results), True))
                return response

        started = time.monotonic()
        metrics: list[ProviderCall] = []
        warnings: list[str] = []
        raw_results: list[SearchResult] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(len(selected), 4))) as pool:
            futures = {pool.submit(self._call_search_provider, provider, query, options): provider for provider in selected}
            for future in concurrent.futures.as_completed(futures):
                provider = futures[future]
                try:
                    results, call = future.result()
                    raw_results.extend(results)
                    metrics.append(call)
                    if call.error:
                        warnings.append(f"{provider}: {call.error}")
                except Exception as exc:
                    metrics.append(ProviderCall(provider, "search", False, 0, error=str(exc)))
                    warnings.append(f"{provider}: {exc}")

        filtered = self._filter_results(raw_results, options)
        deduped = dedupe_results(filtered)
        ranked = rerank_results(query, deduped, options)
        final = ranked[: options.max_results]

        if options.fetch_pages and options.fetch_limit > 0:
            self._fetch_into_results(final[: options.fetch_limit], max_chars=9000)

        sources = ordered_sources(final, selected)
        response = SearchResponse(
            query=query,
            results=final,
            sources=sources,
            metrics=sorted(metrics, key=lambda m: selected.index(m.provider) if m.provider in selected else 99),
            warnings=warnings,
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        if options.use_cache:
            self.cache.set("search", cache_key, response.to_dict())
        return response

    def research(
        self,
        question: str,
        mode: str = "standard",
        max_results: int = 14,
        fetch_limit: int = 6,
        use_cache: bool = True,
    ) -> ResearchBundle:
        mode, cleaned = parse_research_mode(question, fallback_mode=mode)
        queries = build_research_queries(cleaned, mode)
        combined: list[SearchResult] = []
        metrics: list[ProviderCall] = []
        warnings: list[str] = []
        started = time.monotonic()

        per_query = max(6, min(10, max_results))
        for q in queries:
            response = self.search(
                q,
                SearchOptions(
                    max_results=per_query,
                    mode=f"research:{mode}",
                    use_cache=use_cache,
                    freshness_days=45 if mode in {"verify", "compare"} else None,
                ),
            )
            combined.extend(response.results)
            metrics.extend(response.metrics)
            warnings.extend(response.warnings)

        ranked = rerank_results(cleaned, dedupe_results(combined), SearchOptions(mode=f"research:{mode}"))
        final = ranked[:max_results]
        self._fetch_into_results(final[:fetch_limit], max_chars=10000)
        fetched_count = sum(1 for r in final if r.fetched_text)
        sources = ordered_sources(final, ("searxng", "brave", "tavily", "exa"))
        response = SearchResponse(
            query=cleaned,
            results=final,
            sources=sources,
            metrics=metrics,
            warnings=dedupe_warnings(warnings),
            elapsed_ms=int((time.monotonic() - started) * 1000),
        )
        return ResearchBundle(cleaned, mode, queries, response, fetched_count)

    def fetch(self, url: str, options: FetchOptions | None = None) -> FetchResult:
        options = options or FetchOptions()
        selected = self._select_fetch_providers(options)
        cache_key = {
            "kind": "fetch",
            "url": canonicalize_url(url),
            "providers": selected,
            "max_chars": options.max_chars,
        }
        if options.use_cache:
            cached = self.cache.get("fetch", cache_key, options.ttl_seconds)
            if cached:
                result = FetchResult.from_dict(cached)
                result.cached = True
                return result

        last_error = ""
        for provider in selected:
            started = time.monotonic()
            result = self._call_fetch_provider(provider, url, options)
            result.latency_ms = int((time.monotonic() - started) * 1000)
            if result.success and result.text.strip():
                if len(result.text) > options.max_chars:
                    result.text = result.text[: options.max_chars]
                if options.use_cache:
                    self.cache.set("fetch", cache_key, result.to_dict())
                return result
            last_error = result.error or f"{provider} returned no text"
        return FetchResult(url=url, success=False, error=last_error or "no fetch providers available")

    def _select_search_providers(self, options: SearchOptions) -> tuple[str, ...]:
        if options.providers:
            return tuple(dict.fromkeys(options.providers))
        status = self.configured_providers()
        providers = ["searxng"]
        if status["brave"]:
            providers.append("brave")
        if status["tavily"]:
            providers.append("tavily")
        if status["exa"]:
            providers.append("exa")
        return tuple(providers)

    def _select_fetch_providers(self, options: FetchOptions) -> tuple[str, ...]:
        if options.providers:
            return tuple(dict.fromkeys(options.providers))
        status = self.configured_providers()
        providers: list[str] = []
        if status["firecrawl"]:
            providers.append("firecrawl")
        if status["jina"]:
            providers.append("jina")
        if options.allow_browser:
            providers.append("playwright")
        providers.append("urllib")
        return tuple(providers)

    def _call_search_provider(
        self,
        provider: str,
        query: str,
        options: SearchOptions,
    ) -> tuple[list[SearchResult], ProviderCall]:
        started = time.monotonic()
        try:
            if provider == "searxng":
                results = self._search_searxng(query, options)
            elif provider == "brave":
                if not configured_value(self.env.get("BRAVE_SEARCH_API_KEY")):
                    raise RuntimeError("BRAVE_SEARCH_API_KEY not configured")
                results = self._search_brave(query, options)
            elif provider == "tavily":
                if not configured_value(self.env.get("TAVILY_API_KEY")):
                    raise RuntimeError("TAVILY_API_KEY not configured")
                results = self._search_tavily(query, options)
            elif provider == "exa":
                if not configured_value(self.env.get("EXA_API_KEY")):
                    raise RuntimeError("EXA_API_KEY not configured")
                results = self._search_exa(query, options)
            else:
                raise RuntimeError(f"unsupported provider: {provider}")
            elapsed = int((time.monotonic() - started) * 1000)
            return results, ProviderCall(provider, "search", True, elapsed, len(results), approx_cost_units=1.0)
        except Exception as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            return [], ProviderCall(provider, "search", False, elapsed, error=str(exc))

    def _call_fetch_provider(self, provider: str, url: str, options: FetchOptions) -> FetchResult:
        try:
            if provider == "firecrawl":
                if not configured_value(self.env.get("FIRECRAWL_API_KEY")):
                    return FetchResult(url=url, source=provider, success=False, error="FIRECRAWL_API_KEY not configured")
                return self._fetch_firecrawl(url, options)
            if provider == "jina":
                if not configured_value(self.env.get("JINA_API_KEY")):
                    return FetchResult(url=url, source=provider, success=False, error="JINA_API_KEY not configured")
                return self._fetch_jina(url, options)
            if provider == "playwright":
                return self._fetch_playwright(url, options)
            if provider == "urllib":
                return self._fetch_urllib(url, options)
            return FetchResult(url=url, source=provider, success=False, error=f"unsupported fetch provider: {provider}")
        except Exception as exc:
            return FetchResult(url=url, source=provider, success=False, error=str(exc))

    def _search_searxng(self, query: str, options: SearchOptions) -> list[SearchResult]:
        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "engines": "google,duckduckgo,bing",
            "safesearch": "0",
        }
        url = self.env.get("SEARXNG_URL", DEFAULT_SEARXNG_URL).rstrip("/") + "/search"
        data = self._json_get(url, params, {"User-Agent": "Adwi/1.0"}, timeout=12)
        results: list[SearchResult] = []
        for item in data.get("results", [])[: options.max_results]:
            item_url = item.get("url", "")
            if not item_url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item_url,
                    snippet=(item.get("content") or "")[:800],
                    source="searxng",
                    query=query,
                    published_date=item.get("publishedDate") or item.get("published_date") or "",
                )
            )
        return results

    def _search_brave(self, query: str, options: SearchOptions) -> list[SearchResult]:
        params = {
            "q": query,
            "count": min(max(options.max_results, 1), 20),
            "safesearch": "moderate",
            "search_lang": "en",
            "spellcheck": "1",
            "text_decorations": "false",
        }
        data = self._json_get(
            "https://api.search.brave.com/res/v1/web/search",
            params,
            {
                "Accept": "application/json",
                "X-Subscription-Token": self.env.get("BRAVE_SEARCH_API_KEY", ""),
                "User-Agent": "Adwi/1.0",
            },
            timeout=15,
        )
        results: list[SearchResult] = []
        for item in data.get("web", {}).get("results", [])[: options.max_results]:
            item_url = item.get("url", "")
            if not item_url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item_url,
                    snippet=(item.get("description") or "")[:800],
                    source="brave",
                    query=query,
                    published_date=item.get("age", ""),
                )
            )
        return results

    def _search_tavily(self, query: str, options: SearchOptions) -> list[SearchResult]:
        payload: dict[str, Any] = {
            "api_key": self.env.get("TAVILY_API_KEY", ""),
            "query": query,
            "search_depth": "advanced" if options.mode.startswith("research") else "basic",
            "max_results": min(max(options.max_results, 1), 20),
            "include_answer": False,
            "include_raw_content": False,
        }
        if options.include_domains:
            payload["include_domains"] = list(options.include_domains)
        if options.exclude_domains:
            payload["exclude_domains"] = list(options.exclude_domains)
        data = self._json_post(
            "https://api.tavily.com/search",
            payload,
            {"Content-Type": "application/json", "User-Agent": "Adwi/1.0"},
            timeout=18,
        )
        results: list[SearchResult] = []
        for item in data.get("results", [])[: options.max_results]:
            item_url = item.get("url", "")
            if not item_url:
                continue
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item_url,
                    snippet=(item.get("content") or item.get("raw_content") or "")[:800],
                    source="tavily",
                    query=query,
                    published_date=item.get("published_date") or item.get("publishedDate") or "",
                    score=float(item.get("score") or 0.0),
                )
            )
        return results

    def _search_exa(self, query: str, options: SearchOptions) -> list[SearchResult]:
        payload: dict[str, Any] = {
            "query": query,
            "numResults": min(max(options.max_results, 1), 20),
            "type": "auto",
            "contents": {
                "text": {"maxCharacters": 700},
                "highlights": True,
            },
        }
        if options.include_domains:
            payload["includeDomains"] = list(options.include_domains)
        if options.exclude_domains:
            payload["excludeDomains"] = list(options.exclude_domains)
        if options.freshness_days:
            start = datetime.now(timezone.utc) - timedelta(days=options.freshness_days)
            payload["startPublishedDate"] = start.isoformat()
        data = self._json_post(
            "https://api.exa.ai/search",
            payload,
            {
                "Content-Type": "application/json",
                "x-api-key": self.env.get("EXA_API_KEY", ""),
                "User-Agent": "Adwi/1.0",
            },
            timeout=18,
        )
        results: list[SearchResult] = []
        for item in data.get("results", [])[: options.max_results]:
            item_url = item.get("url", "")
            if not item_url:
                continue
            highlights = item.get("highlights") or []
            snippet = item.get("text") or item.get("summary") or " ".join(str(h) for h in highlights[:2])
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item_url,
                    snippet=snippet[:800],
                    source="exa",
                    query=query,
                    published_date=item.get("publishedDate") or item.get("published_date") or "",
                    metadata={"exa_id": item.get("id", ""), "request_id": data.get("requestId", "")},
                )
            )
        return results

    def _fetch_firecrawl(self, url: str, options: FetchOptions) -> FetchResult:
        payload = {"url": url, "formats": ["markdown"]}
        data = self._json_post(
            "https://api.firecrawl.dev/v1/scrape",
            payload,
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.env.get('FIRECRAWL_API_KEY', '')}",
                "User-Agent": "Adwi/1.0",
            },
            timeout=30,
        )
        if not data.get("success"):
            return FetchResult(url=url, source="firecrawl", success=False, error=data.get("error", "unknown error"))
        inner = data.get("data", {})
        meta = inner.get("metadata", {})
        text = inner.get("markdown") or inner.get("text") or ""
        return FetchResult(url=url, title=meta.get("title", ""), text=text[: options.max_chars], source="firecrawl", success=bool(text))

    def _fetch_jina(self, url: str, options: FetchOptions) -> FetchResult:
        normalized = re.sub(r"^https?://", "", url.strip())
        reader_url = "https://r.jina.ai/http://" + normalized
        headers = {
            "Accept": "text/plain",
            "Authorization": f"Bearer {self.env.get('JINA_API_KEY', '')}",
            "User-Agent": "Adwi/1.0",
        }
        text = self._text_get(reader_url, headers, timeout=25)
        title = ""
        for line in text.splitlines()[:8]:
            if line.startswith("Title:"):
                title = line.partition(":")[2].strip()
                break
        return FetchResult(url=url, title=title, text=text[: options.max_chars], source="jina", success=bool(text.strip()))

    def _fetch_playwright(self, url: str, options: FetchOptions) -> FetchResult:
        from playwright.sync_api import sync_playwright  # type: ignore

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            title = page.title()
            text = page.evaluate(
                "() => Array.from(document.querySelectorAll('article,main,p,h1,h2,h3,li'))"
                ".map(e => e.innerText).filter(Boolean).join('\\n')"
            )
            browser.close()
        return FetchResult(url=url, title=title, text=(text or "")[: options.max_chars], source="playwright", success=bool((text or "").strip()))

    def _fetch_urllib(self, url: str, options: FetchOptions) -> FetchResult:
        html = self._text_get(url, {"User-Agent": "Mozilla/5.0"}, timeout=18)
        title = ""
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
        if title_match:
            title = re.sub(r"\s+", " ", title_match.group(1)).strip()
        text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S | re.I)
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return FetchResult(url=url, title=title, text=text[: options.max_chars], source="urllib", success=bool(text))

    def _fetch_into_results(self, results: list[SearchResult], max_chars: int) -> None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(len(results), 4))) as pool:
            futures = {pool.submit(self.fetch, r.url, FetchOptions(max_chars=max_chars)): r for r in results if r.url}
            for future in concurrent.futures.as_completed(futures):
                result = futures[future]
                try:
                    fetched = future.result()
                    if fetched.success and fetched.text:
                        result.fetched_text = fetched.text[:max_chars]
                        result.fetch_source = fetched.source
                        if fetched.title and not result.title:
                            result.title = fetched.title
                except Exception:
                    continue

    def _filter_results(self, results: list[SearchResult], options: SearchOptions) -> list[SearchResult]:
        filtered: list[SearchResult] = []
        cutoff = None
        if options.freshness_days:
            cutoff = datetime.now(timezone.utc) - timedelta(days=options.freshness_days)
        for result in results:
            domain = result_domain(result.url)
            if options.include_domains and not domain_matches(domain, options.include_domains):
                continue
            if options.exclude_domains and domain_matches(domain, options.exclude_domains):
                continue
            if cutoff and options.strict_freshness:
                published = parse_date(result.published_date)
                if published and published < cutoff:
                    continue
            filtered.append(result)
        return filtered

    def _json_get(self, url: str, params: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
        query = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{url}?{query}", headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())

    def _json_post(self, url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int) -> dict[str, Any]:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read())

    def _text_get(self, url: str, headers: dict[str, str], timeout: int) -> str:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")


def dedupe_results(results: list[SearchResult]) -> list[SearchResult]:
    by_url: dict[str, SearchResult] = {}
    for result in results:
        key = result.canonical_url or canonicalize_url(result.url)
        if not key:
            continue
        existing = by_url.get(key)
        if not existing:
            result.metadata.setdefault("providers", [result.source] if result.source else [])
            by_url[key] = result
            continue
        providers = existing.metadata.setdefault("providers", [existing.source] if existing.source else [])
        if result.source and result.source not in providers:
            providers.append(result.source)
        if len(result.snippet) > len(existing.snippet):
            existing.snippet = result.snippet
        if not existing.published_date and result.published_date:
            existing.published_date = result.published_date
        existing.score = max(existing.score, result.score)
        existing.trust = max(existing.trust, result.trust)
    return list(by_url.values())


def rerank_results(query: str, results: list[SearchResult], options: SearchOptions | None = None) -> list[SearchResult]:
    options = options or SearchOptions()
    terms = query_terms(query)
    cutoff = None
    if options.freshness_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=options.freshness_days)

    for result in results:
        title_text = result.title.lower()
        snippet_text = result.snippet.lower()
        title_hits = sum(1 for term in terms if term in title_text)
        snippet_hits = sum(1 for term in terms if term in snippet_text)
        provider_weight = SOURCE_WEIGHTS.get(result.source, 0.50)
        provider_count = len(result.metadata.get("providers", [result.source]))
        freshness_boost = 0.0
        if cutoff:
            published = parse_date(result.published_date)
            if published and published >= cutoff:
                freshness_boost = 0.08
        result.trust = result.trust or trust_score(result.url)
        result.score = (
            provider_weight
            + min(title_hits * 0.10, 0.30)
            + min(snippet_hits * 0.04, 0.20)
            + (provider_count - 1) * 0.05
            + result.trust * 0.18
            + freshness_boost
            + min(float(result.score or 0.0), 1.0) * 0.08
        )
    return sorted(results, key=lambda r: (r.score, r.trust, r.title), reverse=True)


def ordered_sources(results: list[SearchResult], provider_order: tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    for result in results:
        providers = result.metadata.get("providers") or [result.source]
        for provider in providers:
            if provider:
                seen.add(provider)
    return [p for p in provider_order if p in seen] + sorted(seen.difference(provider_order))


def dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for warning in warnings:
        if warning and warning not in seen:
            seen.add(warning)
            out.append(warning)
    return out


def parse_research_mode(text: str, fallback_mode: str = "standard") -> tuple[str, str]:
    q = text.strip()
    lowered = q.lower()
    patterns = [
        ("dig_deeper", r"^(dig\s+deeper(?:\s+into|\s+on)?|deep\s+dive(?:\s+into|\s+on)?)\s+"),
        ("verify", r"^(verify|fact\s*check|cross[-\s]?check)\s+"),
        ("compare", r"^(compare\s+sources(?:\s+for|\s+on)?|compare)\s+"),
    ]
    for mode, pattern in patterns:
        match = re.match(pattern, lowered, re.I)
        if match:
            cleaned = q[match.end():].strip(" :-")
            return mode, cleaned or q
    return fallback_mode, q


def build_research_queries(question: str, mode: str = "standard") -> list[str]:
    q = question.strip()
    if not q:
        return []
    if mode == "verify":
        candidates = [q, f"{q} official source", f"{q} corrections criticism latest"]
    elif mode == "compare":
        candidates = [q, f"{q} official documentation", f"{q} independent analysis comparison"]
    elif mode == "dig_deeper":
        candidates = [q, f"{q} technical details implementation", f"{q} limitations tradeoffs"]
    else:
        candidates = [q, f"{q} official documentation", f"{q} latest update"]
    return list(dict.fromkeys(candidates))


def build_citation_context(
    results: list[SearchResult],
    max_chars: int = 9000,
    per_source_chars: int = 1800,
) -> tuple[str, list[SearchResult]]:
    cited = [r for r in results if r.fetched_text.strip()]
    parts: list[str] = []
    used = 0
    kept: list[SearchResult] = []
    for idx, result in enumerate(cited, 1):
        body = result.fetched_text.strip()[:per_source_chars]
        section = (
            f"[{idx}] {result.title}\n"
            f"URL: {result.url}\n"
            f"Fetched via: {result.fetch_source or 'unknown'}\n"
            f"Text:\n{body}\n"
        )
        if used + len(section) > max_chars:
            break
        parts.append(section)
        kept.append(result)
        used += len(section)
    return "\n---\n".join(parts), kept


def compact_search_context(results: list[SearchResult], max_results: int = 12) -> str:
    rows = []
    for idx, result in enumerate(results[:max_results], 1):
        rows.append(
            f"[{idx}] {result.title}\n"
            f"URL: {result.url}\n"
            f"Providers: {', '.join(result.metadata.get('providers', [result.source]))}\n"
            f"Score: {result.score:.2f} Trust: {result.trust:.2f}\n"
            f"{result.snippet[:500]}"
        )
    return "\n\n".join(rows)


def metrics_summary(metrics: list[ProviderCall]) -> str:
    if not metrics:
        return "no provider metrics"
    calls = []
    total_cost = 0.0
    for metric in metrics:
        total_cost += metric.approx_cost_units
        status = "cache" if metric.cached else ("ok" if metric.ok else "err")
        calls.append(f"{metric.provider}:{status}:{metric.latency_ms}ms/{metric.result_count}")
    return f"{' | '.join(calls)} | approx_cost_units={total_cost:.1f}"

