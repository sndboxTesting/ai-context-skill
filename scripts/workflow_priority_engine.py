#!/usr/bin/env python3
"""Workflow Priority Engine: Ranks workflows based on importance, usage, and context."""

import json
import os
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(os.environ.get("SUNEEL_WORKSPACE", str(pathlib.Path.home() / "SuneelWorkSpace"))).resolve()
PRIORITY_PATH = ROOT / "brain/system/workflow_priority.json"
GEN_DIR = ROOT / "brain/workflows/generated"
ACTIVE_CONTEXT_PATH = ROOT / "agent-system/state/ACTIVE_CONTEXT.json"
EXECUTION_LOG_PATH = ROOT / "brain/logs/workflow_executions.md"
PERFORMANCE_PATH = ROOT / "brain/system/workflow_performance.json"


def load_json(path: pathlib.Path, default: any) -> any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def save_json(path: pathlib.Path, data: any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

def initialize_or_sync() -> dict:
    """Initialize workflow_priority.json from generated workflows and sync any missing ones."""
    db = load_json(PRIORITY_PATH, {})
    
    if not GEN_DIR.exists():
        return db
        
    # Scan all generated workflows
    for f in GEN_DIR.glob("*.json"):
        try:
            w_data = json.loads(f.read_text())
            slug = w_data.get("slug")
            name = w_data.get("name")
            if slug and slug not in db:
                # Default metrics
                db[slug] = {
                    "name": name,
                    "importance": 0.5,
                    "frequency": 0.1,
                    "recent_usage": 0.1,
                    "success_rate": 1.0,
                    "user_signal": 0.5
                }
        except Exception:
            pass
            
    save_json(PRIORITY_PATH, db)
    return db

def calculate_score(w: dict, current_intent: str, active_goal: str, last_actions: list = None, avg_quality: float = None) -> float:
    """Compute score based on Phase 2, Phase 5 & Outcome Quality (Phase 3)."""
    imp = float(w.get("importance", 0.5))
    freq = float(w.get("frequency", 0.1))
    rec = float(w.get("recent_usage", 0.1))
    succ = float(w.get("success_rate", 1.0))
    sig = float(w.get("user_signal", 0.5))
    
    # Base priority score (Phase 2)
    score = (imp * 0.3) + (freq * 0.2) + (rec * 0.2) + (succ * 0.2) + (sig * 0.1)
    
    # Outcome Quality Boost/Penalty (Phase 3 of last request)
    if avg_quality is not None:
        if avg_quality >= 0.8:
            score += 0.15  # Boost visibility for high quality
        elif avg_quality < 0.5:
            score -= 0.25  # Reduce ranking for poor quality/errors
            
    # Real-Time Context priority override (Phase 1)
    name_lower = w.get("name", "").lower()
    slug_lower = w.get("slug", "").replace("_", " ").lower()
    
    matches_intent = False
    if current_intent and current_intent != "unknown":
        normalized_intent = current_intent.replace("_", " ").lower()
        intent_terms = [t for t in normalized_intent.split() if len(t) > 2]
        if any(term in name_lower or term in slug_lower for term in intent_terms):
            matches_intent = True
            
    matches_last_actions = False
    if last_actions:
        for act in last_actions:
            if not act:
                continue
            act_lower = act.lower()
            act_terms = [t for t in act_lower.split() if len(t) > 2]
            if any(term in name_lower or term in slug_lower for term in act_terms):
                matches_last_actions = True
                break
                
    context_boost = 0.0
    if matches_intent:
        context_boost += 0.4
    if matches_last_actions:
        context_boost += 0.2
        
    # Goal boost (Phase 5 of last request, kept as additional context link)
    goal_boost = 0.0
    if active_goal and active_goal != "None":
        normalized_goal = active_goal.lower()
        goal_terms = [t for t in normalized_goal.split() if len(t) > 2]
        if any(term in name_lower or term in goal_terms):
            goal_boost = 0.25
            
    final_score = score + context_boost + goal_boost
    return round(final_score, 3)

def get_ranked_workflows(limit: int = 5) -> list[dict]:
    """Return top workflows based on priority scores and current context."""
    db = initialize_or_sync()
    
    # Read active context
    context = load_json(ACTIVE_CONTEXT_PATH, {})
    intent = context.get("current_intent", "unknown")
    goal = context.get("current_goal", "None")
    last_actions = context.get("last_actions", [])
    
    # Read performance outcomes for quality scoring
    perf_db = load_json(PERFORMANCE_PATH, {})
    
    ranked = []
    for slug, w in db.items():
        # Calculate average quality score from performance history
        perf_runs = perf_db.get(slug, [])
        avg_quality = None
        if perf_runs:
            avg_quality = sum(r.get("quality_score", 1.0) for r in perf_runs) / len(perf_runs)
            
        score = calculate_score(w, intent, goal, last_actions, avg_quality)
        ranked.append({
            "slug": slug,
            "name": w.get("name", slug),
            "priority_score": score,
            "command": f"workflow-{slug.replace('_', '-')}"
        })
        
    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    return ranked[:limit]

def decay_and_boost_workflows():
    """Daily Evolution update (Phase 4): Boost successful workflows, decay unused ones."""
    db = initialize_or_sync()
    
    # Find execution history from logs
    history = {}
    if EXECUTION_LOG_PATH.exists():
        content = EXECUTION_LOG_PATH.read_text(errors="replace")
        # Match lines: ## Workflow Run: <name> - <date>
        # and subsequent status: - **Status**: <SUCCESS/FAILED>
        runs = re.findall(r"## Workflow Run:\s+(.*?)\s+\-\s+\d+.*?Status\*:\s+(\w+)", content, re.DOTALL)
        for run_name, status in runs:
            run_name_clean = run_name.strip()
            # find matching slug
            matched_slug = None
            for slug, w in db.items():
                if w.get("name", "").lower() == run_name_clean.lower():
                    matched_slug = slug
                    break
            
            if matched_slug:
                history.setdefault(matched_slug, []).append(status.upper() == "SUCCESS")
                
    # Update metrics in database
    for slug, w in db.items():
        runs = history.get(slug, [])
        if runs:
            # Boost metrics for active workflows
            # Incremental boosts
            w["frequency"] = min(1.0, float(w.get("frequency", 0.1)) + 0.1 * len(runs))
            w["recent_usage"] = min(1.0, float(w.get("recent_usage", 0.1)) + 0.15 * len(runs))
            
            # Calculate success rate
            successes = sum(1 for r in runs if r)
            w["success_rate"] = round(successes / len(runs), 2)
        else:
            # Decay unused workflows
            w["recent_usage"] = round(max(0.0, float(w.get("recent_usage", 0.1)) * 0.8), 2)
            w["frequency"] = round(max(0.0, float(w.get("frequency", 0.1)) * 0.95), 2)
            
    save_json(PRIORITY_PATH, db)
    print("✓ Workflow priority metrics successfully decayed and boosted based on execution logs.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--decay":
        decay_and_boost_workflows()
    else:
        # Print top workflows for debugging
        top = get_ranked_workflows()
        print(json.dumps(top, indent=2))
