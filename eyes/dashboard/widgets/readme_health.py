"""
README Health Dashboard Widget — returns workspace-wide README health summary.
Reads from spine/readme_health_cache.json (populated by the README update pipeline).
"""
import json
import os
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE", Path(__file__).resolve().parents[3]))
CACHE_PATH = WORKSPACE / "spine/readme_health_cache.json"


def get_readme_health() -> dict:
    result = {
        "overall_score": None,
        "total_folders": 0,
        "healthy_count": 0,
        "warning_count": 0,
        "critical_count": 0,
        "low_health_count": 0,
        "critical_folders": [],
        "last_updated": "",
        "status": "unknown",
    }

    if not CACHE_PATH.exists():
        result["status"] = "cache_missing"
        return result

    try:
        cache = json.loads(CACHE_PATH.read_text())
    except Exception:
        result["status"] = "cache_error"
        return result

    entries = [v for v in cache.values() if "health_score" in v]
    if not entries:
        result["status"] = "no_scores"
        return result

    scores = [v["health_score"] for v in entries]
    result["total_folders"] = len(scores)
    result["overall_score"] = round(sum(scores) / len(scores))
    result["healthy_count"] = sum(1 for s in scores if s >= 80)
    result["warning_count"] = sum(1 for s in scores if 60 <= s < 80)
    result["critical_count"] = sum(1 for s in scores if s < 60)
    result["low_health_count"] = result["critical_count"]

    critical = [
        {"path": k, "score": v["health_score"], "updated": v.get("updated", "")}
        for k, v in cache.items()
        if v.get("health_score", 100) < 60
    ]
    result["critical_folders"] = sorted(critical, key=lambda x: x["score"])[:8]

    timestamps = [v.get("updated", "") for v in cache.values() if v.get("updated")]
    result["last_updated"] = max(timestamps) if timestamps else ""

    overall = result["overall_score"]
    result["status"] = "healthy" if overall >= 80 else ("warning" if overall >= 60 else "critical")

    return result


if __name__ == "__main__":
    print(json.dumps(get_readme_health(), indent=2))
