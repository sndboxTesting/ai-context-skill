#!/usr/bin/env python3
"""
Runtime Probe — safely checks whether Python modules in a folder are importable
and whether shell scripts are syntactically valid. Never executes user code.
"""
import ast
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

WORKSPACE = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True,
    cwd=os.path.dirname(os.path.abspath(__file__))
).strip())


def _check_python_syntax(py_file: Path) -> tuple:
    """Return (ok: bool, error: str)."""
    try:
        ast.parse(py_file.read_text(errors="ignore"))
        return True, ""
    except SyntaxError as e:
        return False, f"{py_file.name}:{e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def _check_shell_syntax(sh_file: Path) -> tuple:
    """Return (ok: bool, error: str). Uses bash -n (dry-run, no execution)."""
    try:
        result = subprocess.run(
            ["bash", "-n", str(sh_file)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def probe_folder(folder_path: str) -> dict:
    """
    Probe a folder for runtime health.
    Returns:
        {
          "importable": list[str],          # .py files with valid syntax
          "broken_imports": list[dict],     # {"file": str, "error": str}
          "runnable_scripts": list[str],    # .sh files passing bash -n
          "broken_scripts": list[dict],     # {"file": str, "error": str}
          "has_tests": bool,
          "python_file_count": int,
          "shell_file_count": int,
        }
    """
    path = Path(folder_path).resolve()
    result = {
        "importable": [],
        "broken_imports": [],
        "runnable_scripts": [],
        "broken_scripts": [],
        "has_tests": False,
        "python_file_count": 0,
        "shell_file_count": 0,
    }

    if not path.is_dir():
        return result

    try:
        for item in sorted(path.iterdir()):
            if not item.is_file():
                continue
            if item.suffix == ".py":
                result["python_file_count"] += 1
                if "test" in item.stem.lower():
                    result["has_tests"] = True
                ok, err = _check_python_syntax(item)
                if ok:
                    result["importable"].append(item.name)
                else:
                    result["broken_imports"].append({"file": item.name, "error": err})
            elif item.suffix == ".sh":
                result["shell_file_count"] += 1
                ok, err = _check_shell_syntax(item)
                if ok:
                    result["runnable_scripts"].append(item.name)
                else:
                    result["broken_scripts"].append({"file": item.name, "error": err})
    except PermissionError:
        pass

    return result


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Runtime probe a folder")
    parser.add_argument("folder", help="Folder to probe")
    args = parser.parse_args()
    print(json.dumps(probe_folder(args.folder), indent=2))
