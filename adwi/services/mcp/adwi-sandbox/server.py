"""
Adwi Sandbox MCP Server
Exposes workspace tools to any MCP-compatible client (Claude Code, n8n, etc.)
Safe read/execute operations only — no destructive or financial actions.
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit("Run with: uv run --with mcp python3 server.py")

WORKSPACE = Path.home() / "SuneelWorkSpace"
SAFE_API  = "http://127.0.0.1:5055"

def _load_workspace_env():
    env_path = WORKSPACE / "adwi" / "config" / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and v:
            os.environ.setdefault(k, v)

_load_workspace_env()
SECRET = os.environ.get("ADWI_LOCAL_SECRET", "")

mcp = FastMCP("adwi-sandbox")

sys.path.insert(0, str(WORKSPACE / "adwi"))
from path_validator import PathValidator as _PathValidator  # noqa: E402

_home = Path.home()
_PATH_VALIDATOR = _PathValidator(
    allowed_roots=[WORKSPACE, _home / "Desktop", _home / "Documents", _home / "Downloads"],
    blocked_roots=[
        WORKSPACE / "secrets",
        WORKSPACE / "adwi" / "config" / ".env",  # contains API keys — not safe to expose via MCP
        _home / ".ssh",
        _home / ".gnupg",
        _home / ".aws",
        _home / ".kube",
        _home / ".config" / "gcloud",
        _home / ".npmrc",
        _home / ".netrc",
        _home / "Library" / "Keychains",
        _home / "Library" / "Passwords",
        Path("/etc"),
        Path("/private"),
        Path("/System"),
        Path("/usr/lib"),
    ],
)


def _safe_api(route: str, body: dict | None = None) -> str:
    url = f"{SAFE_API}{route}"
    try:
        headers = {}
        if SECRET:
            headers["X-Adwi-Secret"] = SECRET
        if body:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
            req = urllib.request.Request(url, data=data, headers=headers)
        else:
            req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=35) as r:
            return r.read().decode()
    except urllib.error.URLError:
        return "Safe Command API is not running. Start it with: cd ~/SuneelWorkSpace && python3 local-command-api/server.py"


@mcp.tool()
def run_python(code: str) -> str:
    """Execute Python code in a temporary file (30s timeout). Returns stdout + stderr + exit code."""
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp = f.name
        r = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=30,
            cwd=str(WORKSPACE),
            env={**os.environ, "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"},
        )
        parts = []
        if r.stdout:
            parts.append(r.stdout.rstrip())
        if r.stderr:
            parts.append(f"[stderr]\n{r.stderr.rstrip()}")
        parts.append(f"[exit {r.returncode}]")
        return "\n".join(parts)
    except subprocess.TimeoutExpired:
        return "Error: timed out after 30s"
    except Exception as e:
        return f"Error: {e}"
    finally:
        if tmp:
            Path(tmp).unlink(missing_ok=True)


@mcp.tool()
def run_bash(command: str) -> str:
    """Execute an allowed bash command via Adwi's safe command allowlist."""
    return (
        "run_bash is not currently implemented in this MCP sandbox. "
        "The adwi CLI (/run-bash) provides shell execution with risk classification "
        "and interactive safety gates that are not portable to the MCP context. "
        "Use the adwi CLI directly, or use the git_status / read_file / list_files tools for read-only operations."
    )


@mcp.tool()
def search_notes(query: str, max_results: int = 5) -> str:
    """Semantic search over Adwi's notes and documents using RAG."""
    script = f"""
import sys
sys.path.insert(0, '{WORKSPACE}/adwi')
try:
    from adwi_cli import cmd_rag
    cmd_rag('{query.replace("'", "")}', top_k={max_results})
except Exception as e:
    print(f'RAG error: {{e}}')
"""
    try:
        r = subprocess.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=20, cwd=str(WORKSPACE)
        )
        return (r.stdout or r.stderr or "No results").strip()
    except subprocess.TimeoutExpired:
        return "RAG search timed out"


@mcp.tool()
def git_status(repo_name: str = "") -> str:
    """Get git status for a workspace repository. Leave blank to list all repos."""
    if repo_name:
        repo = WORKSPACE / repo_name
        if not (repo / ".git").exists():
            return f"No git repo found at {repo}"
        r = subprocess.run(["git", "-C", str(repo), "status", "--short"], capture_output=True, text=True, timeout=10)
        log = subprocess.run(["git", "-C", str(repo), "log", "--oneline", "-5"], capture_output=True, text=True, timeout=10)
        return f"=== {repo_name} ===\n{r.stdout}\nRecent commits:\n{log.stdout}"
    else:
        repos = [d.name for d in sorted(WORKSPACE.iterdir()) if d.is_dir() and (d / ".git").exists()]
        return "Git repos in workspace:\n" + "\n".join(f"  • {r}" for r in repos) if repos else "No git repos found"


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the workspace (workspace-relative or absolute under /Users/MAC)."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / path
    ok, reason = _PATH_VALIDATOR.check(p)
    if not ok:
        return f"Access denied: {reason}"
    if not p.exists():
        return f"File not found: {p}"
    if p.stat().st_size > 500_000:
        return f"File too large ({p.stat().st_size // 1024}KB). Read specific lines instead."
    return p.read_text(errors="replace")


@mcp.tool()
def list_files(directory: str = "", pattern: str = "*") -> str:
    """List files in a workspace directory."""
    p = Path(directory) if directory else WORKSPACE
    if not p.is_absolute():
        p = WORKSPACE / directory
    ok, reason = _PATH_VALIDATOR.check(p)
    if not ok:
        return f"Access denied: {reason}"
    if not p.exists():
        return f"Directory not found: {p}"
    items = sorted(p.glob(pattern))[:100]
    return "\n".join(str(i.relative_to(WORKSPACE) if WORKSPACE in i.parents else i) for i in items)


@mcp.tool()
def adwi_status() -> str:
    """Check which Adwi services are running (Ollama, Open WebUI, n8n, SearXNG, Qdrant)."""
    services = {
        "Ollama":     "http://localhost:11434",
        "Open WebUI": "http://localhost:3000",
        "n8n":        "http://localhost:5678",
        "SearXNG":    "http://localhost:8888",
        "Qdrant":     "http://localhost:6333",
        "Safe API":   "http://localhost:5055",
    }
    lines = []
    for name, url in services.items():
        try:
            urllib.request.urlopen(url, timeout=2)
            lines.append(f"  ✓ {name} — {url}")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                lines.append(f"  ✓ {name} — {url} (auth required)")
            else:
                lines.append(f"  ✗ {name} — HTTP {e.code}")
        except Exception:
            lines.append(f"  ✗ {name} — offline")
    return "\n".join(lines)


@mcp.tool()
def note_append(title: str, content: str) -> str:
    """Append a note to Adwi's notes folder."""
    notes = WORKSPACE / "notes"
    notes.mkdir(exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60]
    path = notes / f"{safe_title}.md"
    with path.open("a") as f:
        f.write(f"\n{content}\n")
    return f"Note saved to {path.name}"


if __name__ == "__main__":
    mcp.run()
