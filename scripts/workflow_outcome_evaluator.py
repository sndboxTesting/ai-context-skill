#!/usr/bin/env python3
"""Workflow Outcome Evaluation System: evaluates runs and manages performance history."""

import json
import os
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(os.environ.get("SUNEEL_WORKSPACE", str(pathlib.Path.home() / "SuneelWorkSpace"))).resolve()
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

def evaluate_quality(success: bool, errors: list[str], steps_outputs: dict[str, str] | list[str]) -> float:
    """Evaluate quality score (0-1) based on completions, correctness, and errors."""
    if not success:
        # Heavily penalize failure
        return 0.1
        
    score = 1.0
    
    # 1. Deduct for any error messages recorded
    if errors:
        score -= min(0.4, 0.15 * len(errors))
        
    # 2. Check steps outputs
    outputs_to_check = []
    if isinstance(steps_outputs, dict):
        outputs_to_check = list(steps_outputs.values())
    elif isinstance(steps_outputs, list):
        outputs_to_check = steps_outputs
        
    for out in outputs_to_check:
        if not out:
            continue
            
        out_lower = out.lower()
        
        # Penalize placeholder/skipped steps
        if "[skipped]" in out_lower or "[none]" in out_lower or out.strip() == "[]":
            score -= 0.1
            
        # Penalize extremely short / empty-like results
        if len(out.strip()) < 10:
            score -= 0.05
            
        # Penalize common error patterns
        error_keywords = ["failed", "error", "exception", "traceback", "syntaxerror", "could not", "permission denied"]
        found_kws = [kw for kw in error_keywords if kw in out_lower]
        if found_kws:
            score -= min(0.3, 0.1 * len(found_kws))
            
    # Ensure score is within [0.0, 1.0] range
    return max(0.0, min(1.0, round(score, 2)))

def record_outcome(workflow_slug: str, success: bool, execution_time: float, errors: list[str], steps_outputs: dict[str, str] | list[str]) -> float:
    """Evaluate, save performance, and return the computed quality score."""
    quality_score = evaluate_quality(success, errors, steps_outputs)
    
    db = load_json(PERFORMANCE_PATH, {})
    
    record = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "success": success,
        "quality_score": quality_score,
        "execution_time": round(execution_time, 2),
        "errors": errors
    }
    
    db.setdefault(workflow_slug, []).append(record)
    # Bounded history to last 20 runs
    db[workflow_slug] = db[workflow_slug][-20:]
    
    save_json(PERFORMANCE_PATH, db)
    print(f"✓ Recorded outcome for '{workflow_slug}' (quality: {quality_score}, success: {success})")
    
    # Sync with workflow_priority.json to update the performance-aware ranking immediately
    try:
        import workflow_priority_engine
        workflow_priority_engine.initialize_or_sync()
    except Exception:
        pass
        
    return quality_score
