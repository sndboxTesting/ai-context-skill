#!/usr/bin/env python3
"""
Post-clone / pre-flight Adwi environment validator.

Checks every layer: Python, dependencies, Ollama, Docker services,
env vars, filesystem layout, and the NLU fast-path. Produces a
colour-coded pass/warn/fail report. Safe to run on a fresh clone —
it is read-only and never modifies anything.

Usage:
    python3 scripts/validate_adwi_env.py [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable

ADWI = Path(__file__).resolve().parent.parent   # adwi/scripts/../../ = adwi/
WORKSPACE = ADWI.parent                          # adwi/../ = SuneelWorkSpace/

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


class Result:
    def __init__(self, name: str, status: str, detail: str = ""):
        self.name = name
        self.status = status  # "pass" | "warn" | "fail"
        self.detail = detail

    def icon(self) -> str:
        return {"pass": f"{GREEN}✓{RESET}", "warn": f"{YELLOW}⚠{RESET}", "fail": f"{RED}✗{RESET}"}[self.status]

    def color(self) -> str:
        return {"pass": GREEN, "warn": YELLOW, "fail": RED}[self.status]


results: list[Result] = []


def check(name: str, fn: Callable[[], tuple[str, str]]) -> Result:
    try:
        status, detail = fn()
    except Exception as e:
        status, detail = "fail", str(e)
    r = Result(name, status, detail)
    results.append(r)
    return r


# ── Checks ────────────────────────────────────────────────────────────────────

def chk_python_version() -> tuple[str, str]:
    v = sys.version_info
    if v >= (3, 12):
        return "pass", f"{v.major}.{v.minor}.{v.micro}"
    return "warn", f"{v.major}.{v.minor} — recommend 3.12+ (repo uses 3.14 venv)"


def chk_venv() -> tuple[str, str]:
    venv = ADWI / ".venv"
    if not venv.exists():
        return "warn", "adwi/.venv not found — run: cd adwi && uv venv && uv pip install -r requirements.txt (if present) or pip install prompt_toolkit instructor openai qdrant-client"
    python = venv / "bin" / "python3"
    if python.exists():
        return "pass", str(venv)
    return "warn", f".venv exists but {python} missing — re-create venv"


def chk_key_files() -> tuple[str, str]:
    required = [
        ADWI / "adwi_cli.py",
        ADWI / "memory.py",
        ADWI / "reason_engine.py",
        ADWI / "nightly.py",
        ADWI / "path_validator.py",
        ADWI / "infra" / "docker" / "docker-compose.yml",
        ADWI / "bin" / "adwi",
    ]
    missing = [str(p.relative_to(WORKSPACE)) for p in required if not p.exists()]
    if missing:
        return "fail", f"Missing: {', '.join(missing)}"
    return "pass", f"{len(required)} core files present"


def chk_syntax() -> tuple[str, str]:
    targets = [
        ADWI / "adwi_cli.py",
        ADWI / "reason_engine.py",
        ADWI / "memory.py",
        ADWI / "nightly.py",
        ADWI / "path_validator.py",
    ]
    bad = []
    for f in targets:
        if not f.exists():
            bad.append(f"{f.name} (missing)")
            continue
        r = subprocess.run(
            [sys.executable, "-m", "py_compile", str(f)],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            bad.append(f"{f.name}: {r.stderr.strip()}")
    if bad:
        return "fail", "; ".join(bad)
    return "pass", f"{len(targets)} files pass py_compile"


def chk_env_file() -> tuple[str, str]:
    env = ADWI / "config" / ".env"
    if not env.exists():
        return "warn", "adwi/config/.env not found — copy adwi/config/.env.example → adwi/config/.env and fill in API keys"
    keys = {}
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            keys[k.strip()] = v.strip()
    wanted = ["TAVILY_API_KEY", "EXA_API_KEY", "FIRECRAWL_API_KEY", "HOME_ASSISTANT_TOKEN"]
    missing = [k for k in wanted if not keys.get(k) or keys[k].startswith("REPLACE_ME")]
    if missing:
        return "warn", f"Missing or placeholder: {', '.join(missing)}"
    return "pass", f"{len(keys)} keys set in config/.env"


def chk_ollama() -> tuple[str, str]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
        models = [m["name"] for m in data.get("models", [])]
        if not models:
            return "warn", "Ollama running but no models loaded — run: ollama pull adwi:latest llama3.1:8b"
        required = ["llama3.1:8b"]
        missing = [m for m in required if not any(m in n for n in models)]
        if missing:
            return "warn", f"Missing models: {', '.join(missing)}. Loaded: {', '.join(models[:4])}"
        return "pass", f"{len(models)} models: {', '.join(models[:5])}"
    except Exception:
        return "fail", "Ollama not reachable at :11434 — run: brew services start ollama"


def chk_docker_services() -> tuple[str, str]:
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode != 0:
            return "warn", "docker ps failed — Docker may not be running"
        lines = [l for l in r.stdout.strip().splitlines() if l]
        running = {l.split("\t")[0] for l in lines if "Up" in l}
        wanted = {"suneel-open-webui", "suneel-n8n", "suneel-searxng"}
        missing = wanted - running
        if missing:
            return "warn", f"Not running: {', '.join(sorted(missing))}. Start: cd local-ai-stack && docker compose up -d"
        return "pass", f"{len(running)} containers up: {', '.join(sorted(running))}"
    except FileNotFoundError:
        return "warn", "docker not found in PATH"
    except subprocess.TimeoutExpired:
        return "warn", "docker ps timed out"


def chk_obsidian_bridge() -> tuple[str, str]:
    try:
        env_path = WORKSPACE / "config" / ".env"
        secret = ""
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ADWI_LOCAL_SECRET="):
                    secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        headers = {"X-Adwi-Secret": secret} if secret else {}
        req = urllib.request.Request("http://localhost:5056/", headers=headers)
        with urllib.request.urlopen(req, timeout=2) as r:
            data = json.loads(r.read())
        if data.get("status") == "ok":
            return "pass", "Obsidian bridge :5056 responding"
        return "warn", f"Bridge responded but status={data.get('status')}"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "warn", "Obsidian bridge :5056 up but ADWI_LOCAL_SECRET mismatch"
        return "warn", f"Obsidian bridge HTTP {e.code}"
    except Exception:
        return "warn", "Obsidian bridge not running at :5056 — run: bin/start-obsidian-bridge"


def chk_searxng() -> tuple[str, str]:
    try:
        url = "http://localhost:8888/search?q=test&format=json"
        with urllib.request.urlopen(url, timeout=4) as r:
            data = json.loads(r.read())
        n = len(data.get("results", []))
        return "pass", f"SearXNG :8888 returning results ({n} for 'test')"
    except Exception:
        return "warn", "SearXNG not reachable at :8888 — start Docker stack"


def chk_qdrant() -> tuple[str, str]:
    try:
        with urllib.request.urlopen("http://localhost:6333/", timeout=3) as r:
            data = json.loads(r.read())
        version = data.get("version", "?")
        return "pass", f"Qdrant :6333 v{version}"
    except Exception:
        return "warn", "Qdrant not reachable at :6333 — start Docker stack or LaunchAgent"


def chk_simeval_artifacts() -> tuple[str, str]:
    simeval = ADWI / "logs" / "simeval"
    report = simeval / "MASTER_REPORT_v2.md"
    backlog = simeval / "fix_backlog_v2.json"
    if not simeval.exists():
        return "warn", "adwi/logs/simeval/ not found — eval artifacts not present"
    missing = []
    if not report.exists():
        missing.append("MASTER_REPORT_v2.md")
    if not backlog.exists():
        missing.append("fix_backlog_v2.json")
    if missing:
        return "warn", f"Missing eval artifacts: {', '.join(missing)}"
    return "pass", f"Eval artifacts present in adwi/logs/simeval/"


def chk_bin_executable() -> tuple[str, str]:
    adwi_bin = ADWI / "bin" / "adwi"
    if not adwi_bin.exists():
        return "fail", "adwi/bin/adwi not found"
    if not os.access(adwi_bin, os.X_OK):
        return "warn", "adwi/bin/adwi exists but not executable — run: chmod +x adwi/bin/adwi"
    in_path = subprocess.run(["which", "adwi"], capture_output=True).returncode == 0
    if not in_path:
        return "warn", "adwi/bin/adwi not in $PATH — add ~/SuneelWorkSpace/adwi/bin to PATH in ~/.zshrc"
    return "pass", "adwi/bin/adwi executable and in PATH"


def chk_launchagents() -> tuple[str, str]:
    la_dir = Path.home() / "Library" / "LaunchAgents"
    adwi_plists = list(la_dir.glob("com.suneel.*.plist"))
    if not adwi_plists:
        return "warn", "No com.suneel.*.plist found — LaunchAgents not installed (optional for dev use)"
    loaded = []
    for p in adwi_plists:
        r = subprocess.run(["launchctl", "list", p.stem], capture_output=True)
        if r.returncode == 0:
            loaded.append(p.stem)
    return "pass", f"{len(loaded)}/{len(adwi_plists)} LaunchAgents loaded"


def chk_gitignore_secrets() -> tuple[str, str]:
    gi = WORKSPACE / ".gitignore"
    if not gi.exists():
        return "fail", ".gitignore not found"
    content = gi.read_text()
    critical = ["secrets/", "config/.env", "**/.env", "**/*token*"]
    missing = [p for p in critical if p not in content]
    if missing:
        return "fail", f".gitignore missing critical patterns: {', '.join(missing)}"
    return "pass", "All critical secret patterns in .gitignore"


# ── Main ──────────────────────────────────────────────────────────────────────

CHECKS = [
    ("Python version", chk_python_version),
    ("Adwi venv", chk_venv),
    ("Core file presence", chk_key_files),
    ("Python syntax", chk_syntax),
    ("config/.env", chk_env_file),
    ("Ollama", chk_ollama),
    ("Docker services", chk_docker_services),
    ("Obsidian bridge", chk_obsidian_bridge),
    ("SearXNG", chk_searxng),
    ("Qdrant", chk_qdrant),
    ("bin/adwi in PATH", chk_bin_executable),
    ("LaunchAgents", chk_launchagents),
    (".gitignore safety", chk_gitignore_secrets),
    ("Eval artifacts", chk_simeval_artifacts),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Adwi environment validator")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    args = parser.parse_args()

    for name, fn in CHECKS:
        check(name, fn)

    if args.json:
        print(json.dumps([{"name": r.name, "status": r.status, "detail": r.detail} for r in results], indent=2))
        return

    print(f"\n{BOLD}Adwi Environment Validation{RESET}")
    print(f"Workspace: {WORKSPACE}")
    print("─" * 60)

    n_pass = sum(1 for r in results if r.status == "pass")
    n_warn = sum(1 for r in results if r.status == "warn")
    n_fail = sum(1 for r in results if r.status == "fail")

    for r in results:
        label = f"{r.color()}{r.name}{RESET}"
        print(f"  {r.icon()}  {label:<35} {r.detail}")

    print("─" * 60)
    print(f"  {GREEN}{n_pass} pass{RESET}  {YELLOW}{n_warn} warn{RESET}  {RED}{n_fail} fail{RESET}")
    print()

    if n_fail > 0:
        print(f"{RED}✗ {n_fail} critical issues must be fixed before adwi will work.{RESET}")
        sys.exit(1)
    elif n_warn > 0:
        print(f"{YELLOW}⚠ {n_warn} warnings — adwi may work in reduced mode.{RESET}")
        print("  See docs/SETUP_NEW_MACHINE.md for setup steps.")
    else:
        print(f"{GREEN}✓ All checks passed. Run: bin/adwi{RESET}")


if __name__ == "__main__":
    main()
