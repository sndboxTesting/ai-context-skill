#!/usr/bin/env python3
"""
Obsidian Bridge — local HTTP API for vault read/write/search.
Runs on 127.0.0.1:5056. Zero external dependencies (stdlib only).

Routes:
  GET  /                          health + vault stats
  GET  /read?path=<rel>           read a note (path relative to vault root)
  GET  /list?dir=<rel>            list notes in a vault subdirectory
  GET  /search?q=<query>          full-text search across all .md files
  POST /write                     write (create/overwrite) a note
                                  body: {"path": "rel/path.md", "content": "..."}
  POST /append                    append content to an existing note
                                  body: {"path": "rel/path.md", "content": "..."}
  POST /daily-note                append/create today's daily note
                                  body: {"content": "..."}

All paths must be INSIDE the vault. Path traversal is rejected.
"""

import json
import os
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

def _load_env():
    """Load config/.env into os.environ (setdefault — does not override shell env)."""
    env_path = Path(__file__).resolve().parents[3] / "config" / ".env"  # adwi/config/.env
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

VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH", "/Users/MAC/SuneelWorkSpace/obsidian-vault"))
HOST  = "127.0.0.1"
PORT  = int(os.environ.get("OBSIDIAN_BRIDGE_PORT", "5056"))


def _safe_path(rel: str) -> Path | None:
    """Return absolute path inside vault, or None if traversal detected."""
    try:
        p = (VAULT / rel).resolve()
        p.relative_to(VAULT.resolve())  # raises ValueError if outside vault
        return p
    except (ValueError, Exception):
        return None


def _vault_stats() -> dict:
    total = sum(1 for _ in VAULT.rglob("*.md"))
    dirs  = [d.name for d in VAULT.iterdir() if d.is_dir() and not d.name.startswith(".")]
    return {"vault": str(VAULT), "total_notes": total, "top_dirs": sorted(dirs)}


def _full_text_search(query: str, max_results: int = 20) -> list:
    q = query.lower().strip()
    results = []
    for md in VAULT.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
            if q in text.lower():
                # Find surrounding context
                idx   = text.lower().find(q)
                start = max(0, idx - 80)
                end   = min(len(text), idx + 160)
                snippet = text[start:end].replace("\n", " ").strip()
                results.append({
                    "path":    str(md.relative_to(VAULT)),
                    "snippet": snippet,
                    "size":    len(text),
                })
                if len(results) >= max_results:
                    break
        except Exception:
            continue
    return results


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _check_auth(self) -> bool:
        if not SECRET:
            return True
        return self.headers.get("X-Adwi-Secret") == SECRET

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        if not self._check_auth():
            return self._json(401, {"error": "Unauthorized — X-Adwi-Secret header required"})
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query)
        route  = parsed.path.rstrip("/") or "/"

        if route == "":
            route = "/"

        if route == "/":
            self._json(200, {"service": "Adwi Obsidian Bridge", "status": "ok",
                             "port": PORT, **_vault_stats()})

        elif route == "/read":
            rel = qs.get("path", [""])[0]
            if not rel:
                return self._json(400, {"error": "?path= required"})
            p = _safe_path(rel)
            if not p:
                return self._json(403, {"error": "path traversal rejected"})
            if not p.exists():
                return self._json(404, {"error": f"not found: {rel}"})
            self._json(200, {
                "path":     rel,
                "content":  p.read_text(encoding="utf-8", errors="ignore"),
                "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
            })

        elif route == "/list":
            rel = qs.get("dir", [""])[0] or ""
            p = _safe_path(rel) if rel else VAULT
            if not p:
                return self._json(403, {"error": "path traversal rejected"})
            if not p.exists() or not p.is_dir():
                return self._json(404, {"error": f"directory not found: {rel}"})
            notes = sorted(
                str(f.relative_to(VAULT))
                for f in p.rglob("*.md")
            )
            self._json(200, {"dir": rel or "/", "notes": notes, "count": len(notes)})

        elif route == "/search":
            q = qs.get("q", [""])[0].strip()
            if not q:
                return self._json(400, {"error": "?q= required"})
            hits = _full_text_search(q)
            self._json(200, {"query": q, "count": len(hits), "results": hits})

        else:
            self._json(404, {"error": f"unknown route: {route}"})

    def do_POST(self):
        if not self._check_auth():
            return self._json(401, {"error": "Unauthorized — X-Adwi-Secret header required"})
        parsed = urlparse(self.path)
        route  = parsed.path.rstrip("/")
        body   = self._read_body()

        if route == "/write":
            rel     = body.get("path", "")
            content = body.get("content", "")
            if not rel:
                return self._json(400, {"error": "body.path required"})
            p = _safe_path(rel)
            if not p:
                return self._json(403, {"error": "path traversal rejected"})
            p.parent.mkdir(parents=True, exist_ok=True)
            # Backup if exists
            if p.exists():
                bak = p.with_suffix(f".{datetime.now().strftime('%Y%m%d-%H%M%S')}.bak")
                bak.write_bytes(p.read_bytes())
            p.write_text(content, encoding="utf-8")
            self._json(200, {"written": rel, "bytes": len(content.encode("utf-8"))})

        elif route == "/append":
            rel     = body.get("path", "")
            content = body.get("content", "")
            if not rel:
                return self._json(400, {"error": "body.path required"})
            p = _safe_path(rel)
            if not p:
                return self._json(403, {"error": "path traversal rejected"})
            p.parent.mkdir(parents=True, exist_ok=True)
            existing = p.read_text(encoding="utf-8") if p.exists() else ""
            p.write_text(existing + "\n" + content, encoding="utf-8")
            self._json(200, {"appended": rel, "total_bytes": p.stat().st_size})

        elif route == "/daily-note":
            content  = body.get("content", "")
            today    = datetime.now().strftime("%Y-%m-%d")
            rel      = f"daily-notes/{today}.md"
            p        = VAULT / "daily-notes" / f"{today}.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            header   = f"# Daily Note — {today}\n\n" if not p.exists() else ""
            existing = p.read_text(encoding="utf-8") if p.exists() else ""
            p.write_text(existing + header + "\n" + content + "\n", encoding="utf-8")
            self._json(200, {"daily_note": rel, "total_bytes": p.stat().st_size})

        elif route == "/daily-note-update":
            # Marker-replace route — prevents duplicate generated sections.
            # body: {"marker": "ADWI:DAILY-BRIEF", "content": "..."}
            marker   = body.get("marker", "")
            content  = body.get("content", "")
            if not marker:
                self._json(400, {"error": "marker field required"}); return
            today    = datetime.now().strftime("%Y-%m-%d")
            rel      = f"daily-notes/{today}.md"
            p        = VAULT / "daily-notes" / f"{today}.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            _TEMPLATE = (
                f"# {today}\n\n## Current Focus\n\n\n"
                "## Decisions\n\n\n## Ideas\n\n\n"
                "## Bugs / Fixes\n\n\n## Pending Approval\n\n\n"
            )
            existing = p.read_text(encoding="utf-8") if p.exists() else _TEMPLATE
            start_tag = f"<!-- {marker}:START -->"
            end_tag   = f"<!-- {marker}:END -->"
            new_block = f"{start_tag}\n{content}\n{end_tag}"
            if start_tag in existing and end_tag in existing:
                updated = re.sub(
                    re.escape(start_tag) + r".*?" + re.escape(end_tag),
                    new_block, existing, flags=re.DOTALL,
                )
            else:
                updated = existing.rstrip("\n") + "\n\n" + new_block + "\n"
            p.write_text(updated, encoding="utf-8")
            self._json(200, {"daily_note": rel, "total_bytes": p.stat().st_size})

        else:
            self._json(404, {"error": f"unknown route: {route}"})

    def log_message(self, fmt, *args):
        # Suppress default request logging to keep nohup logs clean
        pass


if __name__ == "__main__":
    VAULT.mkdir(parents=True, exist_ok=True)
    if not SECRET:
        print("[WARNING] ADWI_LOCAL_SECRET not set — Obsidian Bridge is unauthenticated.")
    else:
        print("[INFO] Auth enabled — X-Adwi-Secret header required.")
    print(f"Obsidian Bridge running at http://{HOST}:{PORT}")
    print(f"Vault: {VAULT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
