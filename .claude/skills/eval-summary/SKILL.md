---
name: eval-summary
description: Parse and summarize the latest Adwi NLU eval results. Shows pass rates, top failing intents by count, and category breakdown. Works with both P1 and P2 eval sessions. Run after any eval to understand what's failing and why.
metadata:
  disable-model-invocation: true
---

```bash
#!/usr/bin/env bash
set -euo pipefail

SIMEVAL=~/SuneelWorkSpace/adwi/logs/simeval

echo "=== Adwi Eval Summary ==="
echo ""

# Find latest P1 and P2 session dirs
P1=$(ls -td "$SIMEVAL"/large-[0-9]* 2>/dev/null | grep -v "p2" | head -1 || echo "")
P2=$(ls -td "$SIMEVAL"/large-p2-[0-9]* 2>/dev/null | head -1 || echo "")

if [ -z "$P1" ] && [ -z "$P2" ]; then
  echo "No eval sessions found in $SIMEVAL"
  exit 1
fi

summarize_session() {
  local dir="$1"
  local label="$2"
  local summary="$dir/summary.json"
  local clusters="$dir/failure_clusters.json"

  echo "── $label: $(basename $dir) ──"
  if [ ! -f "$summary" ]; then
    echo "  (no summary.json found)"
    return
  fi

  python3 - "$summary" "$clusters" <<'PYEOF'
import json, sys
from pathlib import Path

summary_path = Path(sys.argv[1])
clusters_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

s = json.loads(summary_path.read_text())
total = s.get("total", 0)
passed = s.get("passed", 0)
warned = s.get("warned", 0)
failed = s.get("failed", 0)
rate = s.get("pass_rate_pct", 0)
regex_pct = s.get("regex_hit_pct", 0)

print(f"  Pass rate : {rate:.1f}%  ({passed}/{total} pass, {warned} warn, {failed} fail)")
print(f"  Regex hits: {regex_pct:.1f}%  |  LLM calls: {s.get('llm_calls',0)}")
print(f"  Avg latency: {s.get('avg_latency_ms',0):.0f}ms  |  p95: {s.get('p95_latency_ms',0):.0f}ms")

cats = s.get("category_stats", {})
if cats:
    print("")
    print("  Category breakdown (failing):")
    failing_cats = [(k, v) for k, v in cats.items() if v.get("fail", 0) > 0]
    for cat, v in sorted(failing_cats, key=lambda x: -x[1].get("fail", 0)):
        t, p, f = v.get("total",0), v.get("pass",0), v.get("fail",0)
        pct = p/t*100 if t else 0
        print(f"    {cat:<20} {pct:5.1f}% ({f} fail / {t} total)")

if clusters_path and clusters_path.exists():
    clusters = json.loads(clusters_path.read_text())
    if clusters:
        print("")
        print("  Top failure clusters:")
        for c in clusters[:5]:
            intent = c.get("expected_intent", "?")
            count = c.get("fail_count", 0)
            routed = c.get("routed_to", {})
            top_route = max(routed, key=routed.get) if routed else "?"
            examples = c.get("examples", [])[:2]
            print(f"    {intent:<25} {count} fail → mostly routed to '{top_route}'")
            for ex in examples:
                print(f"      e.g. \"{ex}\"")
PYEOF
  echo ""
}

[ -n "$P1" ] && summarize_session "$P1" "P1 large eval"
[ -n "$P2" ] && summarize_session "$P2" "P2 weak-family eval"

echo "Baseline: P1=96.7% | P2=98.2% | Combined=~97.0%  (CYCLE-6, 2026-06-17)"
echo "Run /adwi-check for fast syntax+Gmail test, or the full eval with run_large_eval.py"
```
