#!/bin/zsh
PID_FILE="/tmp/obsidian-bridge.pid"
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" && echo "Obsidian Bridge stopped (PID $PID)"
    else
        echo "Obsidian Bridge was not running"
    fi
    rm -f "$PID_FILE"
else
    echo "No PID file found — Obsidian Bridge may not be running"
fi
