"""
Unit tests for the shared Adwi search orchestrator.

These tests intentionally avoid live external network calls.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from adwi.search_orchestrator import (
    FetchOptions,
    FetchResult,
    ProviderCall,
    SearchCache,
    SearchOptions,
    SearchOrchestrator,
    SearchResponse,
    SearchResult,
    build_citation_context,
    build_research_queries,
    canonicalize_url,
    dedupe_results,
    provider_status,
    rerank_results,
)


class TestUrlNormalization(unittest.TestCase):
    def test_canonicalize_strips_tracking_fragment_and_www(self):
        got = canonicalize_url("HTTPS://www.Example.com/a/?utm_source=x&b=2&a=1#section")
        self.assertEqual(got, "https://example.com/a?a=1&b=2")

    def test_dedupe_combines_provider_metadata(self):
        rows = dedupe_results([
            SearchResult("A", "https://www.example.com/path?utm_campaign=x", "short", "searxng"),
            SearchResult("A2", "https://example.com/path", "longer snippet", "brave"),
        ])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].snippet, "longer snippet")
        self.assertEqual(rows[0].metadata["providers"], ["searxng", "brave"])


class TestProviderGating(unittest.TestCase):
    def test_placeholders_do_not_count_as_configured(self):
        status = provider_status({
            "TAVILY_API_KEY": "tvly-REPLACE_ME",
            "EXA_API_KEY": "",
            "FIRECRAWL_API_KEY": "fc-real",
            "BRAVE_SEARCH_API_KEY": "brv-real",
            "JINA_API_KEY": "JINA-REPLACE_ME",
        })
        self.assertFalse(status["tavily"])
        self.assertFalse(status["exa"])
        self.assertTrue(status["firecrawl"])
        self.assertTrue(status["brave"])
        self.assertFalse(status["jina"])


class FakeSearchOrchestrator(SearchOrchestrator):
    def _search_searxng(self, query: str, options: SearchOptions) -> list[SearchResult]:
        return [
            SearchResult("Official Alpha Docs", "https://docs.example.com/alpha?utm_source=x", "alpha setup guide", "searxng", query=query),
            SearchResult("Forum Noise", "https://forum.example.com/alpha", "alpha rumor", "searxng", query=query),
        ]

    def _search_brave(self, query: str, options: SearchOptions) -> list[SearchResult]:
        return [
            SearchResult("Official Alpha Docs", "https://docs.example.com/alpha", "alpha official reference", "brave", query=query),
        ]

    def _search_tavily(self, query: str, options: SearchOptions) -> list[SearchResult]:
        return [
            SearchResult("Recent Alpha Release", "https://news.example.com/alpha", "alpha release notes", "tavily", query=query, published_date="2026-06-01"),
        ]


class TestSearchOrchestration(unittest.TestCase):
    def test_search_falls_back_across_configured_providers_and_dedupes(self):
        with tempfile.TemporaryDirectory() as td:
            orch = FakeSearchOrchestrator(
                env={
                    "SEARXNG_URL": "http://127.0.0.1:8888",
                    "BRAVE_SEARCH_API_KEY": "brave-real",
                    "TAVILY_API_KEY": "tvly-real",
                },
                cache_dir=Path(td),
            )
            response = orch.search("alpha docs", SearchOptions(max_results=5, use_cache=False))
        urls = [r.canonical_url for r in response.results]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn("brave", response.sources)
        self.assertIn("tavily", response.sources)
        official = next(r for r in response.results if r.canonical_url == "https://docs.example.com/alpha")
        self.assertCountEqual(official.metadata["providers"], ["searxng", "brave"])

    def test_domain_include_and_exclude_filters(self):
        with tempfile.TemporaryDirectory() as td:
            orch = FakeSearchOrchestrator(env={"SEARXNG_URL": "x"}, cache_dir=Path(td))
            included = orch.search(
                "alpha",
                SearchOptions(max_results=5, include_domains=("docs.example.com",), use_cache=False),
            )
            self.assertEqual([r.url for r in included.results], ["https://docs.example.com/alpha?utm_source=x"])

            excluded = orch.search(
                "alpha",
                SearchOptions(max_results=5, exclude_domains=("forum.example.com",), use_cache=False),
            )
            self.assertTrue(all("forum.example.com" not in r.url for r in excluded.results))

    def test_strict_freshness_drops_parseable_old_results(self):
        stale = SearchResult("Old", "https://old.example.com", "alpha", "searxng", published_date="2020-01-01")
        fresh = SearchResult("Fresh", "https://fresh.example.com", "alpha", "searxng", published_date="2026-06-01")
        with tempfile.TemporaryDirectory() as td:
            orch = SearchOrchestrator(env={"SEARXNG_URL": "x"}, cache_dir=Path(td))
            filtered = orch._filter_results(
                [stale, fresh],
                SearchOptions(freshness_days=60, strict_freshness=True),
            )
        self.assertEqual([r.title for r in filtered], ["Fresh"])

    def test_local_rerank_prefers_query_match_and_trust(self):
        weak = SearchResult("Unrelated", "https://forum.example.com/other", "nothing here", "searxng")
        strong = SearchResult("Alpha Install Guide", "https://docs.example.com/alpha", "alpha install setup docs", "searxng")
        ranked = rerank_results("alpha install", [weak, strong])
        self.assertEqual(ranked[0].title, "Alpha Install Guide")


class TestCacheAndFetch(unittest.TestCase):
    def test_cache_respects_ttl(self):
        with tempfile.TemporaryDirectory() as td:
            cache = SearchCache(Path(td))
            key = {"q": "alpha"}
            cache.set("search", key, {"ok": True})
            self.assertEqual(cache.get("search", key, ttl_seconds=60), {"ok": True})

            path = cache._path("search", key)
            path.write_text(json.dumps({"created": time.time() - 120, "payload": {"ok": True}}), encoding="utf-8")
            self.assertIsNone(cache.get("search", key, ttl_seconds=1))

    def test_fetch_falls_back_from_firecrawl_to_jina(self):
        with tempfile.TemporaryDirectory() as td:
            orch = SearchOrchestrator(
                env={"FIRECRAWL_API_KEY": "fc-real", "JINA_API_KEY": "jina-real"},
                cache_dir=Path(td),
            )
            with patch.object(
                orch,
                "_fetch_firecrawl",
                return_value=FetchResult("https://example.com", source="firecrawl", success=False, error="blocked"),
            ), patch.object(
                orch,
                "_fetch_jina",
                return_value=FetchResult("https://example.com", title="Example", text="Fetched text", source="jina", success=True),
            ):
                result = orch.fetch(
                    "https://example.com",
                    FetchOptions(providers=("firecrawl", "jina"), use_cache=False),
                )
        self.assertTrue(result.success)
        self.assertEqual(result.source, "jina")
        self.assertEqual(result.text, "Fetched text")


class TestResearchAndCitations(unittest.TestCase):
    def test_research_query_modes_are_deterministic(self):
        self.assertEqual(build_research_queries("alpha", "verify")[1], "alpha official source")
        self.assertIn("independent analysis comparison", build_research_queries("alpha", "compare")[2])

    def test_research_decomposes_and_fetches_ranked_pages(self):
        with tempfile.TemporaryDirectory() as td:
            orch = FakeSearchOrchestrator(env={"SEARXNG_URL": "x"}, cache_dir=Path(td))
            with patch.object(
                orch,
                "fetch",
                side_effect=lambda url, options=None: FetchResult(url, title="Fetched", text=f"evidence for {url}", source="test", success=True),
            ):
                bundle = orch.research("verify alpha", max_results=6, fetch_limit=4, use_cache=False)
        self.assertEqual(bundle.mode, "verify")
        self.assertGreater(len(bundle.queries), 1)
        self.assertGreaterEqual(bundle.fetched_count, 1)
        self.assertTrue(any(r.fetched_text for r in bundle.results))

    def test_citation_context_only_uses_fetched_text(self):
        fetched = SearchResult("Fetched", "https://a.example.com", "snippet", "searxng", fetched_text="grounded text", fetch_source="test")
        snippet_only = SearchResult("Snippet", "https://b.example.com", "snippet", "searxng")
        context, cited = build_citation_context([fetched, snippet_only])
        self.assertIn("grounded text", context)
        self.assertNotIn("b.example.com", context)
        self.assertEqual(cited, [fetched])


class TestReasonEngineAlignment(unittest.TestCase):
    def test_reason_engine_uses_shared_orchestrator(self):
        import adwi.reason_engine as reason_engine

        class FakeReasonOrchestrator:
            def search(self, query: str, options: SearchOptions) -> SearchResponse:
                self.query = query
                self.options = options
                return SearchResponse(
                    query=query,
                    results=[SearchResult("Shared Result", "https://example.com", "shared snippet", "fake")],
                    sources=["fake"],
                    metrics=[ProviderCall("fake", "search", True, 1, 1)],
                )

        with patch.object(reason_engine, "SearchOrchestrator", FakeReasonOrchestrator):
            ledger = reason_engine.AchievementLedger("search")
            ok, output = reason_engine._exec_web_search("alpha", ledger)
        self.assertTrue(ok)
        self.assertIn("Shared Result", output)
        self.assertEqual(ledger.searches, ["alpha"])


if __name__ == "__main__":
    unittest.main()
