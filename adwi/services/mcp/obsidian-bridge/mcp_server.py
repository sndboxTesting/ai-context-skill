"""
Obsidian Bridge MCP Server
Wraps the obsidian-bridge HTTP API (:5056) as MCP tools for Claude Code.
Run with: uv run --with mcp python3 mcp_server.py
"""
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit("Run with: uv run --with mcp python3 mcp_server.py")

WORKSPACE = Path.home() / "SuneelWorkSpace"
BRIDGE_URL = "http://127.0.0.1:5056"


def _load_env():
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


_load_env()
SECRET = os.environ.get("ADWI_LOCAL_SECRET", "")

mcp = FastMCP("obsidian")


def _get(route: str) -> str:
    try:
        headers = {"X-Adwi-Secret": SECRET} if SECRET else {}
        req = urllib.request.Request(f"{BRIDGE_URL}{route}", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except urllib.error.URLError as e:
        return f"Obsidian bridge offline (start with mcp-servers/obsidian-bridge/start.sh): {e}"


def _post(route: str, body: dict) -> str:
    try:
        headers = {"Content-Type": "application/json"}
        if SECRET:
            headers["X-Adwi-Secret"] = SECRET
        data = json.dumps(body).encode()
        req = urllib.request.Request(f"{BRIDGE_URL}{route}", data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except urllib.error.URLError as e:
        return f"Obsidian bridge offline (start with mcp-servers/obsidian-bridge/start.sh): {e}"


@mcp.tool()
def obsidian_health() -> str:
    """Check Obsidian vault health and stats (total notes, top directories)."""
    return _get("/")


@mcp.tool()
def obsidian_search(query: str, max_results: int = 20) -> str:
    """Full-text search across all Obsidian vault notes. Returns matching notes with context snippets."""
    q = urllib.parse.quote(query)
    return _get(f"/search?q={q}&max_results={max_results}")


@mcp.tool()
def obsidian_read(path: str) -> str:
    """Read a note from the Obsidian vault. Path is relative to vault root (e.g. 'daily/2026-06-17.md')."""
    p = urllib.parse.quote(path)
    return _get(f"/read?path={p}")


@mcp.tool()
def obsidian_list(directory: str = "") -> str:
    """List notes in an Obsidian vault directory. Leave directory empty to list root."""
    d = urllib.parse.quote(directory)
    return _get(f"/list?dir={d}")


@mcp.tool()
def obsidian_write(path: str, content: str) -> str:
    """Create or overwrite a note in the Obsidian vault. Path is relative to vault root."""
    return _post("/write", {"path": path, "content": content})


@mcp.tool()
def obsidian_append(path: str, content: str) -> str:
    """Append content to an existing Obsidian vault note."""
    return _post("/append", {"path": path, "content": content})


@mcp.tool()
def obsidian_daily_note(content: str) -> str:
    """Append content to today's Obsidian daily note (creates it if needed)."""
    return _post("/daily-note", {"content": content})


if __name__ == "__main__":
    mcp.run()
