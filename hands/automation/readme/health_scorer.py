#!/usr/bin/env python3
"""
Health Scorer — computes a 0-100 health score for a workspace folder.

Score breakdown (deductions from 100):
  -20  README missing
  -10  README missing required sections (Purpose / Contents / Change Log)
  -15  README older than folder contents (drift)
  -10  Stale file references in README Contents section
  -15  Broken Python syntax (per broken file, capped at -30)
  -10  Broken shell script syntax (per broken file, capped at -20)
  -10  No test coverage when Python files exist
  -5   Missing Capabilities section
"""
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

WORKSPACE = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
).strip())

REQUIRED_SECTIONS = ["Purpose", "Contents", "Change Log"]


def _readme_mtime(folder: Path) -> float:
    readme = folder / "README.md"
    return readme.stat().st_mtime if readme.exists() else 0.0


def _folder_max_mtime(folder: Path) -> float:
    max_mtime = 0.0
    try:
        for item in folder.iterdir():
            if item.name in {"README.md", ".DS_Store"} or item.name.startswith("."):
                continue
            try:
                max_mtime = max(max_mtime, item.stat().st_mtime)
            except Exception:
                pass
    except Exception:
        pass
    return max_mtime


def _stale_file_refs(readme_content: str, folder: Path) -> list:
    match = re.search(r"## 📂 Contents(.*?)(?=\n## |\Z)", readme_content, re.DOTALL)
    if not match:
        return []
    stale = []
    for m in re.finditer(r"`([^`/]+\.[a-zA-Z0-9]+)`", match.group(1)):
        fname = m.group(1)
        if not (folder / fname).exists():
            stale.append(fname)
    return stale


def score_folder(folder_path: str, analysis: dict = None, probe: dict = None) -> dict:
    """
    Compute health score for a folder.

    Args:
        folder_path: absolute or relative path to folder
        analysis: from intelligence_engine.analyze_folder (recomputed if None)
        probe: from runtime_probe.probe_folder (recomputed if None)

    Returns:
        {
          "score": int,           # 0-100
          "breakdown": dict,      # category → deduction amount
          "critical_issues": list[str],
          "folder": str,
          "timestamp": str,
        }
    """
    path = Path(folder_path).resolve()
    deductions = {}
    issues = []

    if analysis is None:
        from hands.automation.readme.intelligence_engine import analyze_folder
        analysis = analyze_folder(str(path))

    if probe is None:
        from hands.automation.readme.runtime_probe import probe_folder
        probe = probe_folder(str(path))

    readme_path = path / "README.md"

    if not readme_path.exists():
        deductions["readme_missing"] = 20
        issues.append("README.md is missing")
    else:
        try:
            content = readme_path.read_text(errors="ignore")
        except Exception:
            content = ""

        # Required sections
        missing_secs = [s for s in REQUIRED_SECTIONS if s.lower() not in content.lower()]
        if missing_secs:
            deductions["missing_sections"] = 10
            issues.append(f"README missing sections: {missing_secs}")

        # Drift
        readme_mtime = _readme_mtime(path)
        folder_mtime = _folder_max_mtime(path)
        if folder_mtime > readme_mtime + 1:
            deductions["readme_drift"] = 15
            issues.append("README is older than folder contents")

        # Stale file references
        stale = _stale_file_refs(content, path)
        if stale:
            deductions["stale_refs"] = 10
            issues.append(f"Stale file references: {stale}")

        # Capabilities section
        if "capabilit" not in content.lower():
            deductions["no_capabilities"] = 5

    # Broken Python
    broken_py = probe.get("broken_imports", [])
    if broken_py:
        penalty = min(30, 15 * len(broken_py))
        deductions["broken_python"] = penalty
        for b in broken_py:
            issues.append(f"Syntax error in {b['file']}: {b['error'][:60]}")

    # Broken shell scripts
    broken_sh = probe.get("broken_scripts", [])
    if broken_sh:
        penalty = min(20, 10 * len(broken_sh))
        deductions["broken_shell"] = penalty
        for b in broken_sh:
            issues.append(f"Shell error in {b['file']}: {b['error'][:60]}")

    # No tests
    if probe.get("python_file_count", 0) > 0 and not probe.get("has_tests", False):
        deductions["no_tests"] = 10
        issues.append("No test files detected")

    total_deduction = sum(deductions.values())
    score = max(0, min(100, 100 - total_deduction))

    try:
        rel = str(path.relative_to(WORKSPACE))
    except ValueError:
        rel = str(path)

    return {
        "score": score,
        "breakdown": deductions,
        "critical_issues": issues,
        "folder": rel,
        "timestamp": datetime.now().isoformat(),
    }


def score_all_folders(workspace_root: str = None) -> list:
    from hands.automation.readme.intelligence_engine import analyze_workspace
    root = Path(workspace_root) if workspace_root else WORKSPACE
    analyses = analyze_workspace(str(root))
    results = []
    for analysis in analyses:
        folder = str(root / analysis["path"])
        try:
            result = score_folder(folder, analysis=analysis)
            results.append(result)
        except Exception:
            pass
    return sorted(results, key=lambda x: x["score"])


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Score README health for a folder")
    parser.add_argument("folder", nargs="?", help="Folder to score (default: top 10 worst)")
    args = parser.parse_args()

    if args.folder:
        result = score_folder(args.folder)
        print(json.dumps(result, indent=2))
    else:
        results = score_all_folders()
        print(f"Scored {len(results)} folders — bottom 10:")
        for r in results[:10]:
            print(f"  {r['score']:3d}/100  {r['folder']}")
