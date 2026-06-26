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
