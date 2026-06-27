#!/usr/bin/env python3
"""
Change Impact Engine — given a list of changed files, determines which workspace
folders need README updates using semantic analysis:

  1. Direct: the folder containing the changed file
  2. Cascade: folders that import from / depend on the changed folder (via dep map)
  3. Python import scan: detect which organs a changed .py file imports from
  4. Organ root: organ-level folder is always included when a sub-folder changes
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

WORKSPACE = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
).strip())

ORGANS = {
    "brain", "heart", "eyes", "ears", "nervous", "skeleton",
    "blood", "hands", "mouth", "dna", "lab", "spine",
}

IGNORED = {".git", "node_modules", ".venv", "__pycache__", "nerve_inbox", "logs"}
IGNORED_EXTS = {".log", ".jsonl", ".pyc", ".out.log", ".err.log"}

DEP_MAP_PATH = WORKSPACE / "spine/readme_dependency_map.json"


def _load_dep_map() -> dict:
    if DEP_MAP_PATH.exists():
        try:
            data = json.loads(DEP_MAP_PATH.read_text())
            return data.get("folders", {})
        except Exception:
            pass
    return {}


def _organ_of(folder: Path) -> str:
    try:
        parts = folder.relative_to(WORKSPACE).parts
        return parts[0] if parts and parts[0] in ORGANS else ""
    except ValueError:
        return ""


def _get_python_organ_imports(changed_file: Path) -> list:
    """Parse Python file and return list of organ names it imports from."""
    if not changed_file.exists() or changed_file.suffix != ".py":
        return []
    refs = []
    try:
        tree = ast.parse(changed_file.read_text(errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in ORGANS:
                        refs.append(root)
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                if root in ORGANS:
                    refs.append(root)
    except Exception:
        pass
    return list(set(refs))


def get_impacted_folders(changed_files: list) -> list:
    """
    Given a list of changed file paths (relative to WORKSPACE), return an
    ordered list of absolute folder Paths that need README updates.

    Order: direct containing folders → cascade from dep map → imported organs

    Args:
        changed_files: relative path strings, e.g. ["brain/memory/store.py"]

    Returns:
        list[Path] — deduplicated, ordered
    """
    dep_map = _load_dep_map()
    seen_rels = set()
    result: list = []

    def _add(folder: Path) -> None:
        if not folder.is_dir():
            return
        try:
            rel = str(folder.relative_to(WORKSPACE))
        except ValueError:
            return
        if rel not in seen_rels:
            seen_rels.add(rel)
            result.append(folder)

    for file_str in changed_files:
        if not file_str:
            continue

        p = Path(file_str)
        # Skip non-code files
        if p.suffix in IGNORED_EXTS or p.name == "README.md":
            continue
        if any(part in IGNORED for part in p.parts):
            continue
        if len(p.parts) > 5:
            continue

        # Direct containing folder
        folder = (WORKSPACE / file_str).resolve().parent
        _add(folder)

        # Organ root folder
        organ = _organ_of(folder)
        if organ:
            _add(WORKSPACE / organ)

        # Cascade from dependency map
        try:
            folder_rel = str(folder.relative_to(WORKSPACE))
        except ValueError:
            folder_rel = ""

        if folder_rel:
            for rdep in dep_map.get(folder_rel, {}).get("reverse_dependencies", []):
                _add(WORKSPACE / rdep)

        # Python import-based cascade
        full_path = WORKSPACE / file_str
        for ref_organ in _get_python_organ_imports(full_path):
            _add(WORKSPACE / ref_organ)

    return result


def explain_impact(changed_files: list) -> None:
    impacted = get_impacted_folders(changed_files)
    print(f"Changed: {changed_files}")
    print(f"Impacted folders ({len(impacted)}):")
    for p in impacted:
        try:
            rel = p.relative_to(WORKSPACE)
        except ValueError:
            rel = p
        print(f"  → {rel}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Show README update cascade for changed files")
    parser.add_argument("files", nargs="+", help="Changed files (relative to workspace root)")
    args = parser.parse_args()
    explain_impact(args.files)
