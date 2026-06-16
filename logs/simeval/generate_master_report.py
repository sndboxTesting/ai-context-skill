#!/usr/bin/env python3
"""
Generate a combined MASTER REPORT from one or more large-eval sessions.
Usage: python3 logs/simeval/generate_master_report.py [session_dirs...]
If no args, auto-discovers all large-* and large-p2-* sessions.
"""
from __future__ import annotations
import json, sys, datetime
from collections import Counter, defaultdict
from pathlib import Path

OUTBASE = Path(__file__).parent
TODAY   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def load_all_results(session_dirs: list[Path]) -> list[dict]:
    results = []
    for d in session_dirs:
        rj = d / "results.jsonl"
        if rj.exists():
            for line in rj.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    r["_session"] = d.name
                    results.append(r)
    return results

def deduplicate(results: list[dict]) -> list[dict]:
    """Remove exact prompt duplicates, keeping first occurrence."""
    seen: set[str] = set()
    out = []
    for r in results:
        key = r["prompt"].lower().strip()
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out

def main():
    if sys.argv[1:]:
        session_dirs = [Path(a) for a in sys.argv[1:]]
    else:
        session_dirs = sorted(OUTBASE.glob("large-*"))

    print(f"Loading from {len(session_dirs)} sessions: {[d.name for d in session_dirs]}")
    all_results = load_all_results(session_dirs)
    print(f"Total raw results: {len(all_results)}")
    results = deduplicate(all_results)
    print(f"After dedup: {len(results)}")

    n = len(results)
    passed  = [r for r in results if r["verdict"] == "pass"]
    warned  = [r for r in results if r["verdict"] == "warn"]
    failed  = [r for r in results if r["verdict"] == "fail"]
    regex_h = [r for r in results if r["router"] == "regex"]
    llm_c   = [r for r in results if r["router"] == "llm"]
    errors_ = [r for r in results if r["router"] == "error"]

    pass_rate = round(100 * len(passed) / n, 1)
    regex_pct = round(100 * len(regex_h) / n, 1)

    latencies = [r["latency_ms"] for r in results]
    avg_lat = round(sum(latencies) / len(latencies), 1)
    sorted_lat = sorted(latencies)
    p95_lat = sorted_lat[int(0.95 * len(sorted_lat))]

    # Safety
    safety_recs = [r for r in results if "safety" in r.get("tags", []) or r.get("risk_label") == "high"]
    safety_breaches = [r for r in safety_recs if r["verdict"] == "fail"]

    # Category breakdown
    cat_stats: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"total": 0, "pass": 0, "warn": 0, "fail": 0}
        cat_stats[cat]["total"] += 1
        cat_stats[cat][r["verdict"]] += 1

    # Failure clusters
    fail_by_intent: dict[str, list[dict]] = {}
    for r in failed:
        k = r["expected_intent"] or "__none__"
        fail_by_intent.setdefault(k, []).append(r)

    # Mis-route analysis
    misroutes: Counter = Counter()
    for r in failed:
        exp = r["expected_intent"] or "__none__"
        got = r["got_intent"] or "__none__"
        misroutes[(exp, got)] += 1

    # Paraphrase family consistency
    fam_results: dict[str, list] = {}
    for r in results:
        fam = r.get("paraphrase_family")
        if fam:
            fam_results.setdefault(fam, []).append(r["verdict"])

    unstable_fams = []
    for fam, verdicts in fam_results.items():
        total_f = len(verdicts)
        pass_f  = verdicts.count("pass")
        fail_f  = verdicts.count("fail")
        if total_f >= 3 and fail_f > 0:
            pct = round(100 * pass_f / total_f, 1)
            if pct < 90:
                unstable_fams.append({
                    "family": fam,
                    "total": total_f,
                    "pass": pass_f,
                    "fail": fail_f,
                    "consistency_pct": pct,
                })
    unstable_fams.sort(key=lambda x: x["consistency_pct"])

    # Router breakdown
    regex_by_intent: Counter = Counter()
    for r in regex_h:
        regex_by_intent[r["got_intent"]] += 1

    # Compare to baseline
    BASELINE = {"total": 502, "passed": 379, "pass_rate": 75.5, "regex_hits": 218}

    # Latency hotspots
    slow_llm = sorted(llm_c, key=lambda r: -r["latency_ms"])[:15]

    # ── Build candidates for "needs human review" fixes ────────────────────────
    fix_candidates = []

    # Fix 1: file_search too broad
    file_search_victims = [r for r in failed
                           if r["got_intent"] == "file_search"
                           and r["expected_intent"] in ("cleanup","duplicates","large_files","old_files","organize")]
    if file_search_victims:
        fix_candidates.append({
            "id": "FIX-001",
            "title": "file_search regex too broad — swallows cleanup/duplicates/large_files",
            "count": len(file_search_victims),
            "evidence": [r["prompt"] for r in file_search_victims[:5]],
            "root_cause": (
                r"`\b(find|search for|locate|look for)\b.{0,20}\bfiles?\b` matches "
                "'find things to delete', 'find duplicate files', 'find large files'. "
                "The word 'files' appears in disk management prompts but should not trigger file_search."
            ),
            "proposed_fix": (
                "Add negative lookahead to file_search pattern: require file path context "
                "(extension, directory, 'in workspace', 'in /path') OR remove 'find' as standalone trigger. "
                "Alternative: add pre-guards for duplicate/cleanup intents BEFORE file_search in REGEX_INTENTS."
            ),
            "affected_file": "adwi/adwi_cli.py — _REGEX_INTENTS file_search section",
            "effort": "low",
            "confidence": "high",
            "impact": f"~{len(file_search_victims)} scenarios would flip to pass",
        })

    # Fix 2: youtube has no regex
    youtube_fails = fail_by_intent.get("youtube", [])
    if youtube_fails:
        fix_candidates.append({
            "id": "FIX-002",
            "title": "youtube intent has no regex — all go to LLM, most fail",
            "count": len(youtube_fails),
            "evidence": [r["prompt"] for r in youtube_fails[:5]],
            "root_cause": "No regex pattern for youtube in _REGEX_INTENTS. LLM classifies as chat or web_search.",
            "proposed_fix": (
                "Add regex: `(youtube|youtu\\.be|yt video|youtube video).{0,30}(summar|transcript|watch)` → youtube\n"
                "And: `(summar|transcri).{0,20}(youtube|youtu\\.be)` → youtube"
            ),
            "affected_file": "adwi/adwi_cli.py — _REGEX_INTENTS",
            "effort": "low",
            "confidence": "high",
            "impact": f"~{len(youtube_fails)} scenarios would flip to pass",
        })

    # Fix 3: obsidian_search → memory_recall confusion
    obs_to_mem = [r for r in failed
                  if r["expected_intent"] in ("obsidian_search","obsidian_daily")
                  and r["got_intent"] == "memory_recall"]
    if obs_to_mem:
        fix_candidates.append({
            "id": "FIX-003",
            "title": "obsidian_search/daily → memory_recall LLM confusion",
            "count": len(obs_to_mem),
            "evidence": [r["prompt"] for r in obs_to_mem[:5]],
            "root_cause": (
                "LLM sees 'search my notes', 'open my note', 'my daily note' and routes to memory_recall "
                "because _INTENT_SYSTEM description for memory_recall says 'what YOU remember about their setup'. "
                "Notes queries are semantically similar to memory queries."
            ),
            "proposed_fix": (
                "Strengthen _INTENT_SYSTEM: add to obsidian_search rule: "
                "'ALWAYS prefer obsidian_search over memory_recall when the prompt mentions obsidian, vault, or notes with a search action'. "
                "Also add: for memory_recall, explicitly say NOT for obsidian/vault/note search queries."
            ),
            "affected_file": "adwi/adwi_cli.py — _INTENT_SYSTEM",
            "effort": "low",
            "confidence": "medium",
            "impact": f"~{len(obs_to_mem)} scenarios would flip to pass",
        })

    # Fix 4: large_files → disk_usage regression
    large_to_disk = [r for r in failed
                     if r["expected_intent"] == "large_files" and r["got_intent"] == "disk_usage"]
    if large_to_disk:
        fix_candidates.append({
            "id": "FIX-004",
            "title": "large_files → disk_usage regression for some prompts",
            "count": len(large_to_disk),
            "evidence": [r["prompt"] for r in large_to_disk[:5]],
            "root_cause": (
                "Some large_files prompts contain 'disk' or 'space' keywords which trigger disk_usage regex. "
                "Example: 'what's the heaviest stuff on disk' — correctly routes to disk_usage, "
                "but 'heaviest files on disk' should route to large_files."
            ),
            "proposed_fix": (
                "Add additional large_files pattern: "
                r"`\bfiles?\b.{0,30}(heaviest|biggest|largest|most space).{0,20}(disk|drive|ssd)` → large_files "
                "BEFORE disk_usage patterns."
            ),
            "affected_file": "adwi/adwi_cli.py — _REGEX_INTENTS",
            "effort": "low",
            "confidence": "medium",
            "impact": f"~{len(large_to_disk)} scenarios",
        })

    # Fix 5: organize → chat LLM miss
    organize_to_chat = [r for r in failed
                        if r["expected_intent"] == "organize" and r.get("got_intent") in ("chat","file_search")]
    if organize_to_chat:
        fix_candidates.append({
            "id": "FIX-005",
            "title": "organize → chat/file_search LLM miss",
            "count": len(organize_to_chat),
            "evidence": [r["prompt"] for r in organize_to_chat[:5]],
            "root_cause": (
                "organize intent has no explicit rule in _INTENT_SYSTEM. "
                "LLM sees 'help me organize files' as advisory chat, and sometimes as file_search. "
                "The regex covers 'organiz/tidy/restructure' but not all advisory phrasing."
            ),
            "proposed_fix": (
                "Add to _INTENT_SYSTEM: "
                "'organize: user wants help organizing, sorting, restructuring, or tidying their file/folder hierarchy. "
                "Different from cleanup (deletion) and file_search (finding files).'"
            ),
            "affected_file": "adwi/adwi_cli.py — _INTENT_SYSTEM",
            "effort": "low",
            "confidence": "medium",
            "impact": f"~{len(organize_to_chat)} scenarios",
        })

    # Fix 6: benchmark → other confusion
    bench_fails = fail_by_intent.get("benchmark", [])
    if bench_fails:
        fix_candidates.append({
            "id": "FIX-006",
            "title": "benchmark regex too narrow — misses 'how fast is my model'",
            "count": len(bench_fails),
            "evidence": [r["prompt"] for r in bench_fails[:5]],
            "root_cause": (
                "Current benchmark regex requires 'adwi|model|local|ollama' in the same phrase as "
                "'benchmark|speed test|how fast|tokens per second'. "
                "Many benchmark prompts like 'tokens/sec please', 't/s benchmark', "
                "'inference throughput' don't have these keywords."
            ),
            "proposed_fix": (
                "Add: `(tokens?/s|t/s|tok/s|throughput).{0,20}(model|llm|ollama|adwi)?` → benchmark\n"
                "And: `(inference|llm|model|ollama).{0,20}(speed|throughput|latency|benchmark)` → benchmark\n"
                "And: `how fast.{0,20}(llm|model|is adwi|is ollama)` → benchmark"
            ),
            "affected_file": "adwi/adwi_cli.py — _REGEX_INTENTS",
            "effort": "low",
            "confidence": "high",
            "impact": f"~{len(bench_fails)} scenarios",
        })

    # ── Write all artifacts ────────────────────────────────────────────────────
    report_path = OUTBASE / "MASTER_REPORT_v2.md"

    lines = []
    lines.append(f"# Adwi NLU — Master Eval Report v2")
    lines.append(f"*Generated: {TODAY} | Sessions: {', '.join(d.name for d in session_dirs)}*")

    lines.append(f"\n---\n## 1. Run Summary")
    lines.append(f"| Metric | Value | vs Baseline |")
    lines.append(f"|--------|-------|-------------|")
    lines.append(f"| Total scenarios | {n} | +{n - BASELINE['total']} |")
    lines.append(f"| Pass | {len(passed)} ({pass_rate}%) | was {BASELINE['pass_rate']}% |")
    lines.append(f"| Warn | {len(warned)} | — |")
    lines.append(f"| Fail | {len(failed)} | — |")
    lines.append(f"| Errors (LLM/parse) | {len(errors_)} | — |")
    lines.append(f"| Regex fast-path | {len(regex_h)} ({regex_pct}%) | was 43.4% |")
    lines.append(f"| LLM calls | {len(llm_c)} | — |")
    lines.append(f"| Avg latency | {avg_lat}ms | — |")
    lines.append(f"| P95 latency | {p95_lat}ms | — |")
    lines.append(f"| Safety probes | {len(safety_recs)} | — |")
    lines.append(f"| Safety breaches | {len(safety_breaches)} | — |")

    lines.append(f"\n---\n## 2. Category Pass Rates")
    lines.append(f"| Category | Pass | Total | Rate |")
    lines.append(f"|----------|------|-------|------|")
    for cat, s in sorted(cat_stats.items(), key=lambda x: -x[1]["total"]):
        rate = round(100 * s["pass"] / s["total"], 1) if s["total"] else 0
        lines.append(f"| {cat} | {s['pass']} | {s['total']} | {rate}% |")

    lines.append(f"\n---\n## 3. Failure Families")
    for intent, recs in sorted(fail_by_intent.items(), key=lambda x: -len(x[1]))[:25]:
        got_c = Counter(r["got_intent"] or "__none__" for r in recs)
        top_got = ", ".join(f"{g}({c})" for g,c in got_c.most_common(3))
        lines.append(f"\n### `{intent}` — {len(recs)} failures → {top_got}")
        for r in recs[:4]:
            lines.append(f"  - `{r['prompt'][:80]}`")

    lines.append(f"\n---\n## 4. Top Mis-routes (expected → got)")
    lines.append(f"| Pattern | Count |")
    lines.append(f"|---------|-------|")
    for (exp,got), cnt in misroutes.most_common(30):
        lines.append(f"| `{exp}` → `{got}` | {cnt} |")

    lines.append(f"\n---\n## 5. Unstable Paraphrase Families (top 20)")
    lines.append(f"| Family | Consistency | Pass/Total |")
    lines.append(f"|--------|-------------|------------|")
    for f_ in unstable_fams[:20]:
        lines.append(f"| {f_['family']} | {f_['consistency_pct']}% | {f_['pass']}/{f_['total']} |")

    lines.append(f"\n---\n## 6. Safety Summary")
    if safety_breaches:
        lines.append(f"**⚠️  {len(safety_breaches)} safety breach(es) detected:**")
        for r in safety_breaches:
            lines.append(f"  - BREACH: `{r['prompt'][:80]}` → routed to `{r['got_intent']}`")
    else:
        lines.append("✅ No safety breaches detected.")

    lines.append(f"\n---\n## 7. Needs Human Review — Proposed Fixes")
    for fc in fix_candidates:
        lines.append(f"\n### {fc['id']}: {fc['title']}")
        lines.append(f"**Impact:** ~{fc['count']} scenarios | **Effort:** {fc['effort']} | **Confidence:** {fc['confidence']}")
        lines.append(f"\n**Root Cause:** {fc['root_cause']}")
        lines.append(f"\n**Proposed Fix:**\n```\n{fc['proposed_fix']}\n```")
        lines.append(f"\n**File:** `{fc['affected_file']}`")
        lines.append(f"\n**Evidence:**")
        for ex in fc['evidence']:
            lines.append(f"  - `{ex}`")

    lines.append(f"\n---\n## 8. Prioritized Repair Backlog")
    lines.append("Ordered by (estimated_impact × confidence / effort):\n")
    for i, fc in enumerate(sorted(fix_candidates, key=lambda x: -x["count"]), 1):
        lines.append(f"{i}. **{fc['id']}** — {fc['title']} (~{fc['count']} scenarios)")

    lines.append(f"\n---\n## 9. Regex Fast-Path Coverage by Intent")
    lines.append(f"| Intent | Regex hits |")
    lines.append(f"|--------|-----------|")
    for intent, cnt in regex_by_intent.most_common():
        lines.append(f"| {intent} | {cnt} |")

    lines.append(f"\n---\n## 10. Latency Hotspots (top 15 slowest LLM calls)")
    for r in slow_llm:
        lines.append(f"  - {r['latency_ms']:.0f}ms | `{r['prompt'][:60]}`")

    report_path.write_text("\n".join(lines))
    print(f"\nMaster report written: {report_path}")

    # ── Also write machine-readable fix backlog ────────────────────────────────
    backlog_path = OUTBASE / "fix_backlog_v2.json"
    backlog_path.write_text(json.dumps(fix_candidates, indent=2))
    print(f"Fix backlog written: {backlog_path}")

    # ── Summary stats ──────────────────────────────────────────────────────────
    summary_path = OUTBASE / "combined_summary_v2.json"
    summary_path.write_text(json.dumps({
        "sessions": [d.name for d in session_dirs],
        "generated": TODAY,
        "total": n,
        "passed": len(passed),
        "warned": len(warned),
        "failed": len(failed),
        "pass_rate_pct": pass_rate,
        "regex_hits": len(regex_h),
        "regex_hit_pct": regex_pct,
        "llm_calls": len(llm_c),
        "avg_latency_ms": avg_lat,
        "p95_latency_ms": p95_lat,
        "safety_probes": len(safety_recs),
        "safety_breaches": len(safety_breaches),
        "top_misroutes": [{"from": exp, "to": got, "count": cnt}
                           for (exp,got),cnt in misroutes.most_common(30)],
        "fail_by_intent": {k: len(v) for k,v in sorted(fail_by_intent.items(), key=lambda x: -len(x[1]))},
        "fix_candidates": fix_candidates,
        "unstable_families": unstable_fams[:20],
    }, indent=2))
    print(f"Combined summary written: {summary_path}")
    print(f"\n{'='*60}")
    print(f"COMBINED: {n} scenarios | {len(passed)} pass ({pass_rate}%) | {len(failed)} fail")
    print(f"Regex: {len(regex_h)} ({regex_pct}%) | Safety breaches: {len(safety_breaches)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
