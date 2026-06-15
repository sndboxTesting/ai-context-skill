# Rollback & Recovery Guide

**Last Updated:** 2026-06-15
**Purpose:** Restore any component to known-good state without data loss.

---

## Known-Good State (2026-06-15)

```
adwi_cli.py    — NLU dispatch, memory-recall (3-layer), web search, obsidian commands
nightly.py     — 10-step loop: services, logs, AI discovery, aider heal, evals,
                  health audit, web research, memory scan, cap sync, git commit,
                  obsidian daily note, morning brief
overnight_learn.py — 7-hour knowledge indexer (fixed greedy JSON regex)
obsidian-bridge/server.py — vault HTTP API on :5056
knowledge.db   — 2065 Q&A pairs (post 2026-06-15 overnight run)
```

---

## Per-Component Rollback

### adwi_cli.py
```bash
# See all recent changes
git log --oneline adwi/adwi_cli.py

# Roll back to a specific commit
git checkout <commit-hash> -- adwi/adwi_cli.py

# Verify after rollback
python3 -m py_compile adwi/adwi_cli.py && echo "syntax OK"
```

### nightly.py
```bash
git checkout <commit-hash> -- adwi/nightly.py
python3 -m py_compile adwi/nightly.py && echo "syntax OK"
```

### Obsidian Bridge (kill + restart)
```bash
# Stop
/Users/MAC/SuneelWorkSpace/mcp-servers/obsidian-bridge/stop.sh

# Start
/Users/MAC/SuneelWorkSpace/mcp-servers/obsidian-bridge/start.sh

# Or via launchd
launchctl unload ~/Library/LaunchAgents/com.suneel.obsidian-bridge.plist
launchctl load   ~/Library/LaunchAgents/com.suneel.obsidian-bridge.plist
```

### knowledge.db (if corrupted)
```bash
# knowledge.db is gitignored — it cannot be recovered from git.
# To rebuild from scratch, re-run overnight_learn.py:
nohup python3 ~/SuneelWorkSpace/adwi/overnight_learn.py > /tmp/overnight-learn.log 2>&1 &
```

### memory.db (if corrupted)
```bash
# memory.db is gitignored — rebuilt by /memory-scan inside adwi CLI:
adwi
/memory-scan
```

### Docker Stack
```bash
cd ~/SuneelWorkSpace/local-ai-stack
docker compose down
docker compose up -d
# Verify
docker ps
```

### Ollama
```bash
brew services restart ollama
# Verify
curl http://localhost:11434/api/tags
```

### LaunchAgents — reload all
```bash
for plist in ~/Library/LaunchAgents/com.suneel.*.plist; do
  launchctl unload "$plist" 2>/dev/null
  launchctl load "$plist"
  echo "loaded: $plist"
done
```

---

## Emergency: Full System Reset to Last Git Commit

```bash
cd ~/SuneelWorkSpace

# See what would change
git status
git diff

# Roll back all tracked files (does NOT touch gitignored files like .db)
git checkout -- .

# Verify
python3 -m py_compile adwi/adwi_cli.py
python3 -m py_compile adwi/nightly.py
python3 -m py_compile adwi/overnight_learn.py
echo "All clear"
```

---

## Service Endpoint Reference

| Service | URL | Start Command |
|---|---|---|
| Ollama | http://localhost:11434 | `brew services start ollama` |
| Open WebUI | http://localhost:3000 | `docker compose up -d` |
| n8n | http://localhost:5678 | `docker compose up -d` |
| SearXNG | http://localhost:8888 | `docker compose up -d` |
| Qdrant | http://localhost:6333 | `docker compose up -d` |
| Obsidian Bridge | http://localhost:5056 | `bin/start-obsidian-bridge` |
| Local Command API | http://localhost:5055 | `bin/start-command-api` |
| PrivateGPT | http://localhost:8001 | `uv tool run private-gpt serve` |

---

## Validation Checklist (run after any major change)

```bash
# 1. Python syntax
python3 -m py_compile adwi/adwi_cli.py && echo "cli OK"
python3 -m py_compile adwi/nightly.py   && echo "nightly OK"
python3 -m py_compile adwi/overnight_learn.py && echo "overnight OK"
python3 -m py_compile mcp-servers/obsidian-bridge/server.py && echo "bridge OK"

# 2. Services
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; print('Ollama OK:', len(json.load(sys.stdin)['models']), 'models')"
curl -s http://localhost:3000/api/version
curl -s http://localhost:8888/search?q=test&format=json | python3 -c "import sys,json; d=json.load(sys.stdin); print('SearXNG OK:', len(d.get('results',[])),'results')"
curl -s http://localhost:5056/ | python3 -c "import sys,json; d=json.load(sys.stdin); print('Obsidian bridge OK:', d['status'])"

# 3. Quick adwi smoke test
echo "/memory-stats\n/exit" | python3 adwi/adwi_cli.py 2>/dev/null | grep -E "Total|Memory|Error"
```
