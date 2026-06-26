# Workflow: Composed Workflow

**Last Executed**: 2026-06-26T09:07:53.629571-05:00
**Execution Status**: FAILED
**Safety Level**: CONTROLLED

## Structure & Steps
1. search_web_brave "best python AST parsing libraries"
2. filesystem_read_file "scripts/integrity_guard.py"
3. generate_fix
4. search_web_brave "Model Context Protocol best practices"
5. filesystem_read_file "audit/gap_analysis.md"
6. filesystem_read_file "agent-system/state/WORKSPACE_HEALTH.json"
7. github_create_issue "Workspace health check updates"
8. python3 "-m unittest adwi/simlab/tests/test_nlu_regex.py"
9. python3 "adwi/logs/simeval/run_large_eval.py --workers 3"
10. python3 "adwi/logs/simeval/run_large_eval_p2.py --workers 3"
11. python3 "adwi/logs/simeval/generate_master_report.py \"

## Recent Execution Outputs
### Output for step `step_1`
```
[
  {
    "title": "Model Context Protocol",
    "url": "https://modelcontextprotocol.io",
    "snippet": "An open standard that enables developers to build secure, bidirectional connections between AI models and their data sources."
  },
  {
    "title": "Claude Desktop MCP Server Guide",
    "url": "https://github.com/modelcontextprotocol/servers",
    "snippet": "A collection of reference Model Context Protocol servers including GitHub, Brave Search, SQLite, Filesystem, and more."
  }
]
```
### Output for step `step_2`
```
#!/usr/bin/env python3
"""Canonical Integrity Guard: Protects existing core files from internal duplication and bad merges."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("SUNEEL_WORKSPACE", Path.home() / "SuneelWorkSpace")).resolve()

def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)

def extract_python_functions(content: str) -> list[dict[str, Any]]:
    """Extract python function names, body signatures, and line spans using AST parsing."""
    funcs = []
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Simple normalization of body to detect duplicate logic
                body_code = ""
                try:
                    body_code = ast.unparse(node.body)
                except Exception:
                    body_code = str(node.body)
                funcs.append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "body": body_code.strip(),
                    "lineno": node.lineno
                })
    except SyntaxError:
        # Fallback to regex if AST fails (e.g., incomplete edits)
        for match in re.finditer(r"^\s*def\s+(\w+)\s*\((.*?)\):", content, re.MULTILINE):
            funcs.append({
                "name": match.group(1),
                "args": [a.strip() for a in match.group(2).split(",") if a.strip()],
                "body": "",
                "lineno": content.count("\n", 0, match.start()) + 1
            })
    return funcs

def extract_generic_functions(content: str, ext: str) -> list[dict[str, Any]]:
    """Extract functions for non-Python scripts (shell, JS, etc.) using regex."""
    funcs = []
    # Match standard shell/bash functions: `name() {` or `function name {`
    if ext in (".sh", ".bash", ".zsh", ""):
        # Match `func_name() {` or `function func_name {`
        pattern = r"^\s*(?:function\s+)?(\w+)\s*\(\s*\)\s*\{|^\s*function\s+(\w+)\s*(?:\{\s*)?$"
        for match in re.finditer(pattern, content, re.MULTILINE):
            name = match.group(1) or match.group(2)
            if name:
                funcs.append({
                    "name": name,
                    "body": "",
                    "lineno": content.count("\n", 0, match.start()) + 1
                })
    return funcs

def check_internal_duplication(content: str, ext: str) -> list[tuple[str, str]]:
    """Scan content for duplicate function names or duplicate logic blocks."""
    duplicates = []
    if ext == ".py":
        funcs = extract_python_functions(content)
        # Check duplicate names
        seen_names = {}
        for f in funcs:
            name = f["name"]
            if name in seen_names:
                duplicates.append(("function_name", f"Function '{name}' is defined multiple times (lines {seen_names[name]} and {f['lineno']})."))
            else:
                seen_names[name] = f["lineno"]
        
        # Check duplicate bodies (exact logic replication)
        seen_bodies = {}
        for f in funcs:
            body = f["body"]
            if not body or len(body) < 20: # skip empty or tiny helpers
                continue
            if body in seen_bodies:
                duplicates.append(("function_logic", f"Duplicate logic block: Function '{f['name']}' has identical body to '{seen_bodies[body]}'. Check for copy-paste redundancy."))
            else:
                seen_bodies[body] = f["name"]
    else:
        funcs = extract_generic_functions(content, ext)
        seen_names = {}
        for f in funcs:
            name = f["name"]
            if name in seen_names:
                duplicates.append(("function_name", f"Function/Routine '{name}' is defined multiple times (lines {seen_names[name]} and {f['lineno']})."))
            else:
                seen_names[name] = f["lineno"]
                
    return duplicates

def check_proposed_duplication(current_content: str, proposed_content: str, ext: str) -> list[tuple[str, str]]:
    """Compare proposed changes vs current content to see if it introduces duplicate functions."""
    current_funcs = {f["name"]: f for f in (extract_python_functions(current_content) if ext == ".py" else extract_generic_functions(current_content, ext))}
    proposed_funcs = extract_python_functions(proposed_content) if ext == ".py" else extract_generic_functions(proposed_content, ext)
    
    dupes = []
    for pf in proposed_funcs:
        name = pf["name"]
        if name in current_funcs:
            # It's fine to modify a function, but if they both exist in separate places or are exact replicas, warning is raised.
            # Let's check if the body has changed or if it's duplicate logic
            curr_f = current_funcs[name]
            if ext == ".py" and pf["body"] == curr_f["body"] and len(pf["body"]) > 20:
                dupes.append(("redundant_edit", f"Proposed function '{name}' has identical logic to existing function. Merge or extend rather than duplicating."))
    return dupes

def main() -> int:
    parser = argparse.ArgumentParser(description="Canonical Integrity Guard")
    parser.add_argument("target", help="Target file path to check")
    parser.add_argument("--proposed", "-p", help="Proposed new content file to compare against target", default=None)
    parser.add_argument("--override-integrity", action="store_true", help="Bypass integrity warning")
    args = parser.parse_args()
    
    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"Error: Target file '{args.target}' does not exist.", file=sys.stderr)
        return 2
        
    ext = target_path.suffix.lower()
    
    # Read current content
    current_content = target_path.read_text(errors="ignore")
    
    issues = []
    
    # 1. Check current internal duplication
    internal_dupes = check_internal_duplication(current_content, ext)
    for dtype, msg in internal_dupes:
        issues.append((dtype, msg))
        
    # 2. Check proposed edits duplication
    if args.proposed:
        proposed_path = Path(args.proposed).resolve()
        if not proposed_path.exists():
            print(f"Error: Proposed content file '{args.proposed}' does not exist.", file=sys.stderr)
            return 2
        proposed_content = proposed_path.read_text(errors="ignore")
        proposed_dupes = check_proposed_duplication(current_content, proposed_content, ext)
        for dtype, msg in proposed_dupes:
            issues.append((dtype, msg))
            
    if issues and not args.override_integrity:
        print("="*60, file=sys.stderr)
        print("⚠️  Canonical Integrity Warning:", file=sys.stderr)
        print("This change introduces duplicate logic inside an existing system.", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Target: {rel(target_path)}", file=sys.stderr)
        print("\nIntegrity Issues Found:", file=sys.stderr)
        for idx, (itype, msg) in enumerate(issues, 1):
            print(f"  {idx}. [{itype.upper()}] {msg}", file=sys.stderr)
        print("\nOptions:", file=sys.stderr)
        print("  1. Refactor existing implementation instead of duplicating.", file=sys.stderr)
        print("  2. Merge new logic into the existing function.", file=sys.stderr)
        print("  3. Force apply changes (Run command with '--override-integrity').", file=sys.stderr)
        print("="*60, file=sys.stderr)
        return 1
        
    if issues and args.override_integrity:
        print(f"✓ Warning bypassed with --override-integrity for: {rel(target_path)}")
    else:
        print(f"✓ Integrity verification passed: {rel(target_path)}")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
### Output for step `step_3`
```
// PROPOSED FIX FOR workspace integrity
// Inspired by: [
  {
    "title": "Model Context Protocol",
    "url": "htt...
// Modifying local file contents of size: 7978 bytes
print('Integrity Guard Upgraded Successfully')
```
### Output for step `step_4`
```
[
  {
    "title": "Model Context Protocol",
    "url": "https://modelcontextprotocol.io",
    "snippet": "An open standard that enables developers to build secure, bidirectional connections between AI models and their data sources."
  },
  {
    "title": "Claude Desktop MCP Server Guide",
    "url": "https://github.com/modelcontextprotocol/servers",
    "snippet": "A collection of reference Model Context Protocol servers including GitHub, Brave Search, SQLite, Filesystem, and more."
  }
]
```
### Output for step `step_5`
```
# Gap Analysis

Generated: 2026-06-26T09:07:19.066968-05:00

| Category | Priority | Gap | Impact | Suggested Fix |
|---|---:|---|---|---|
| architecture | P0 | System-wide audit artifacts were missing or not first-class. | Agents could inspect files ad hoc, but there was no durable overview for future sessions. | Create audit reports, gap analysis, improvement plan, and MCP resources. |
| automation | P0 | Health checks did not summarize audit/gap/research/tool readiness. | Maintenance could report green while intelligence coverage was incomplete. | Add system-intelligence status and health update hooks. |
| intelligence | P1 | Ideas, comparisons, and decisions had no dedicated pipeline. | Research outcomes could remain in chat instead of becoming durable shared brain context. | Add a local research engine with capture, research, analyze, decide, and bootstrap scripts. |
| research | P1 | Tool discovery was not summarized into an inspectable inventory. | Agents had to rediscover installed CLIs, apps, and integration candidates. | Generate tools/tool_inventory.json and recommendations.md. |
| workflow | P1 | Email, messaging, downloads, and file organization support existed only as scattered commands. | Daily workflows lacked a unified route from capture to execution to memory. | Route workflow ideas through idea-start/idea-run and record decisions in shared brain. |
| usability | P0 | There was no single command for capabilities, gaps, recommendations, or bounded self-upgrade. | Suneel had to know internal paths and command names. | Add system-audit, system-gaps, system-capabilities, system-recommend, and improve-system. |
| architecture | P1 | MCP resource coverage did not include audit, research, profile, and tool artifacts. | Connected agents could miss the new intelligence surfaces. | Register new resources in mcp/server/config/resource_map.json. |
| automation | P1 | Autolab evaluates improvements, but weak-area discovery was not tied to system gaps. | Self-improvement can optimize local prompt/docs while missing architecture-level needs. | Add an autolab strategy note that consumes gap_analysis.md and recommendations.md. |
```
### Output for step `step_6`
```
{
  "auto_fixes_applied": 40,
  "checked_at": "2026-06-26T09:07:20-0500",
  "error_count": 0,
  "issue_count": 0,
  "issues": [],
  "last_doctor_run": "2026-06-26T09:07:20-0500",
  "last_repair_run": "2026-06-26T09:07:21-0500",
  "launchd": {
    "configured": true,
    "label": "com.suneelworkspace.maintenance",
    "loaded": true,
    "plist": "/Users/MAC/Library/LaunchAgents/com.suneelworkspace.maintenance.plist"
  },
  "repair_suggestions": [],
  "state_updated_at": "2026-06-26T09:07:21.008390-05:00",
  "status": "healthy",
  "system_intelligence": {
    "checks": {
      "gap_analysis": true,
      "improvement_plan": true,
      "mcp_resource_coverage": true,
      "research_engine": true,
      "system_audit": true,
      "system_profile": true,
      "tool_inventory": true,
      "tool_recommendations": true
    },
    "ready": true,
    "updated_at": "2026-06-26T09:07:21.008390-05:00"
  },
  "tools": {
    "claude": "/opt/homebrew/bin/claude",
    "codex": "/Users/MAC/bin/codex"
  },
  "warning_count": 0
}
```
### Output for step `step_7`
```
Created GitHub issue successfully: https://github.com/suneeluhcl/SuneelWorkSpace/issues/7
```
### Output for step `step_8`
```
E
======================================================================
ERROR: adwi/simlab/tests/test_nlu_regex (unittest.loader._FailedTest.adwi/simlab/tests/test_nlu_regex)
----------------------------------------------------------------------
ImportError: Failed to import test module: adwi/simlab/tests/test_nlu_regex
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.14/3.14.5/Frameworks/Python.framework/Versions/3.14/lib/python3.14/unittest/loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
ModuleNotFoundError: No module named 'adwi/simlab/tests/test_nlu_regex'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```
