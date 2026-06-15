#!/bin/zsh
# Start the Obsidian Bridge server in the background
SCRIPT_DIR="${0:A:h}"
VAULT_PATH="${OBSIDIAN_VAULT_PATH:-/Users/MAC/SuneelWorkSpace/obsidian-vault}"
PID_FILE="/tmp/obsidian-bridge.pid"
LOG_FILE="/tmp/obsidian-bridge.log"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Obsidian Bridge already running (PID $(cat "$PID_FILE"))"
    exit 0
fi

OBSIDIAN_VAULT_PATH="$VAULT_PATH" \
nohup /opt/homebrew/bin/python3 "$SCRIPT_DIR/server.py" \
    >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
sleep 1
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "Obsidian Bridge started — PID $(cat "$PID_FILE") — http://127.0.0.1:5056"
else
    echo "ERROR: Obsidian Bridge failed to start — check $LOG_FILE"
    exit 1
fi
