#!/usr/bin/env python3
"""Daily Evolution Outcome Scoring.
Captures health score before and after daily-evolve runs, logs delta.
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get('WORKSPACE', Path.home() / 'SuneelWorkSpace'))
SCORES_FILE = WORKSPACE / 'brain/system/evolution_scores.json'
HEALTH_FILE = WORKSPACE / 'agent-system/state/WORKSPACE_HEALTH.json'


def get_health_score() -> float:
    if not HEALTH_FILE.exists():
        return 0.0
    try:
        with open(HEALTH_FILE) as f:
            data = json.load(f)
        # Try direct score fields first
        if 'health_score' in data:
            return float(data['health_score'])
        if 'score' in data:
            return float(data['score'])
        # Compute from issue/error counts
        errors = int(data.get('error_count', 0))
        issues = int(data.get('issue_count', 0))
        return float(max(0, 100 - errors * 20 - issues * 5))
    except Exception:
        return 0.0


def load_scores():
    if not SCORES_FILE.exists():
        return {"scores": []}
    with open(SCORES_FILE) as f:
        return json.load(f)


def save_scores(data):
    SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCORES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def record_evolution(before: float, after: float, actions: list = None):
    data = load_scores()
    delta = round(after - before, 2)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "before": before,
        "after": after,
        "delta": delta,
        "actions_taken": actions or []
    }
    data["scores"].append(entry)
    save_scores(data)
    return entry


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "record"

    if mode == "before":
        score = get_health_score()
        print(f"BEFORE_SCORE={score}")

    elif mode == "after":
        before = float(os.environ.get('BEFORE_SCORE', 0))
        after = get_health_score()
        entry = record_evolution(before, after)
        delta_str = f"+{entry['delta']}" if entry['delta'] >= 0 else str(entry['delta'])
        print(f"Evolution scored: before={before} after={after} delta={delta_str}")

    elif mode == "trend":
        data = load_scores()
        scores = data.get('scores', [])
        if not scores:
            print("No evolution scores yet. Run daily-evolve first.")
            return
        print("\n=== Evolution Trend (last 20 runs) ===")
        print(f"{'Date':<12} {'Before':>7} {'After':>7} {'Delta':>7} {'Bar'}")
        print("-" * 50)
        for s in scores[-20:]:
            delta = s.get('delta', 0)
            bar = "█" * min(int(abs(delta)), 10)
            prefix = "+" if delta >= 0 else "-"
            print(f"{s['date']:<12} {s['before']:>7.1f} {s['after']:>7.1f} {prefix}{abs(delta):>6.1f} {bar}")

        recent = scores[-5:] if len(scores) >= 5 else scores
        avg_delta = sum(s.get('delta', 0) for s in recent) / len(recent)
        trend = "📈 Improving" if avg_delta > 0.5 else ("📉 Declining" if avg_delta < -0.5 else "→ Stable")
        print(f"\n5-run avg delta: {avg_delta:+.2f} — {trend}")


if __name__ == '__main__':
    main()
