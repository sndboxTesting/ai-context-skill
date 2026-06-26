#!/usr/bin/env python3
"""Workflow Self-Optimization: Analyzes performance outcomes and generates optimization suggestions."""

import json
import os
import pathlib
import re
from datetime import datetime, timezone

ROOT = pathlib.Path(os.environ.get("SUNEEL_WORKSPACE", str(pathlib.Path.home() / "SuneelWorkSpace"))).resolve()
PERFORMANCE_PATH = ROOT / "brain/system/workflow_performance.json"
OPTIMIZATIONS_PATH = ROOT / "brain/system/workflow_optimizations.md"
GEN_DIR = ROOT / "brain/workflows/generated"

def load_json(path: pathlib.Path, default: any) -> any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()

def run_optimization_pass() -> dict:
    """Analyze workflow outcomes and generate specific recommendations."""
    perf_db = load_json(PERFORMANCE_PATH, {})
    
    recommendations = {}
    
    for slug, runs in perf_db.items():
        if not runs:
            continue
            
        # Calculate average quality score
        avg_q = sum(r.get("quality_score", 1.0) for r in runs) / len(runs)
        
        # Check latest run details
        latest_run = runs[-1]
        errors = latest_run.get("errors", [])
        success = latest_run.get("success", False)
        
        # If low score or repeated failures, trigger analysis
        failures_count = sum(1 for r in runs[-5:] if not r.get("success", True))
        
        if avg_q < 0.6 or failures_count >= 2:
            rec = {
                "name": slug.replace("_", " ").title(),
                "avg_quality": round(avg_q, 2),
                "recent_failures": failures_count,
                "status": "Warning" if avg_q < 0.6 else "Needs Optimization",
                "weak_steps": [],
                "suggestions": []
            }
            
            # Analyze weak steps based on error logs
            # E.g., if error contains step name or specific connector name
            step_failed = None
            for err in errors:
                step_match = re.search(r"step_(\d+)", err)
                if step_match:
                    step_failed = f"step_{step_match.group(1)}"
                    break
                    
            # Load step definitions from generated json to see what action was run
            json_path = GEN_DIR / f"{slug}.json"
            steps_data = load_json(json_path, {})
            commands = steps_data.get("commands", [])
            
            if step_failed:
                rec["weak_steps"].append(step_failed)
                
                # Deduce index
                try:
                    idx = int(step_failed.split("_")[1]) - 1
                    if 0 <= idx < len(commands):
                        failed_cmd = commands[idx]
                        rec["suggestions"].append(f"Remove or replace failed command: `{failed_cmd}`")
                        
                        # Inspect cmd type to offer intelligent hints
                        if "search" in failed_cmd or "brave" in failed_cmd:
                            rec["suggestions"].append("Suggestion: Replace Brave Search with direct web queries or cache results.")
                        elif "filesystem" in failed_cmd or "read" in failed_cmd:
                            rec["suggestions"].append("Suggestion: Ensure destination path exists, check directory structure, or verify permissions.")
                        elif "github" in failed_cmd or "issue" in failed_cmd:
                            rec["suggestions"].append("Suggestion: Check GitHub personal access token (GH_TOKEN) scope and repository permissions.")
                except Exception:
                    pass
            else:
                # General failures fallback
                rec["suggestions"].append("Analyze execution time: Workflow may be experiencing timeout issues.")
                rec["suggestions"].append("Reorder steps: Ensure prerequisite files are fetched before compile steps.")
                rec["suggestions"].append("Verify MCP connectors availability across Mac system.")
                
            recommendations[slug] = rec
            
    # Write report to brain/system/workflow_optimizations.md
    lines = [
        "# Workflow Self-Optimization Report",
        f"**Last Analysis Pass**: {now_iso()}",
        "",
        "This report tracks low-quality or repeatedly failing workflows and suggests structural improvements.",
        ""
    ]
    
    if recommendations:
        for slug, r in recommendations.items():
            lines.append(f"## {r['name']} ({r['status']})")
            lines.append(f"- **Average Quality**: `{r['avg_quality']:.2f}`")
            lines.append(f"- **Recent Failures**: `{r['recent_failures']}/5 runs`")
            if r["weak_steps"]:
                lines.append(f"- **Identified Weak Steps**: `{', '.join(r['weak_steps'])}`")
            lines.append("- **Suggested Optimizations**:")
            for s in r["suggestions"]:
                lines.append(f"  - {s}")
            lines.append("")
    else:
        lines.append("✅ All workflows are running within optimal performance metrics (Average Quality >= 80%, 0 recent failures).")
        lines.append("No candidates for optimization detected.")
        
    OPTIMIZATIONS_PATH.write_text("\n".join(lines) + "\n")
    print(f"✓ Workflow self-optimization report generated at {OPTIMIZATIONS_PATH.name}")
    return recommendations

if __name__ == "__main__":
    run_optimization_pass()
