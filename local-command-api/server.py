from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import os
from datetime import datetime

HOME = os.path.expanduser("~")
BIN = os.path.join(HOME, "SuneelWorkSpace", "bin")

VENV_PY = os.path.join(HOME, "SuneelWorkSpace", "adwi", ".venv", "bin", "python3")
ADWI_CLI = os.path.join(HOME, "SuneelWorkSpace", "adwi", "adwi_cli.py")

ALLOWED_COMMANDS = {
    "/status-ai":              [os.path.join(BIN, "status-ai")],
    "/daily-ai-status-report": [os.path.join(BIN, "daily-ai-status-report")],
    "/index-ai-notes":         [os.path.join(BIN, "index-ai-notes")],
    "/auto-ai-maintenance":    [os.path.join(BIN, "auto-ai-maintenance")],
    "/adwi-self-heal":         [os.path.join(BIN, "adwi-self-heal")],
    "/rag-index":              [os.path.join(BIN, "rag-index")],
    "/git-status-workspace":   [os.path.join(BIN, "git-status-workspace")],
    "/benchmark-adwi":         [os.path.join(BIN, "benchmark-adwi")],
    # ── Adwi pillar commands (called by n8n + HA dashboard) ──────────────────
    "/adwi-backup":            [VENV_PY, ADWI_CLI, "/backup-now"],
    "/adwi-nightly":           [VENV_PY, ADWI_CLI, "/nightly-run"],
    "/adwi-brief":             [VENV_PY, ADWI_CLI, "/what-next"],
    "/adwi-status":            [VENV_PY, ADWI_CLI, "/status"],
    "/adwi-doctor":            [VENV_PY, ADWI_CLI, "/doctor"],
}

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self._send_json(200, {
                "name": "Suneel Safe Local Command API",
                "time": datetime.now().isoformat(),
                "allowed_routes": sorted(ALLOWED_COMMANDS.keys()),
                "safety": "Only explicitly allowlisted commands can run."
            })
            return

        if self.path not in ALLOWED_COMMANDS:
            self._send_json(404, {
                "error": "Route not allowed",
                "allowed_routes": sorted(ALLOWED_COMMANDS.keys())
            })
            return

        cmd = ALLOWED_COMMANDS[self.path]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900,
                env={
                    **os.environ,
                    "PATH": f"{BIN}:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
                    "SUNEEL_COMMAND_API_CONTEXT": "1"
                }
            )
            self._send_json(200, {
                "route": self.path,
                "command": cmd,
                "returncode": result.returncode,
                "stdout": result.stdout[-12000:],
                "stderr": result.stderr[-4000:]
            })
        except Exception as e:
            self._send_json(500, {
                "route": self.path,
                "error": str(e)
            })

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 5055
    print(f"Suneel Safe Local Command API running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
