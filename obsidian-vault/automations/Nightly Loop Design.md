# Nightly Loop Design

**Trigger:** macOS LaunchAgent `com.suneel.adwi-nightly` at 2:00 AM daily
**Script:** `~/SuneelWorkSpace/adwi/nightly.py`
**Log:** `/tmp/adwi-nightly.log`
**Output:** `~/Desktop/morning_brief.md` + `obsidian-vault/daily-notes/YYYY-MM-DD.md`

---

## Execution Phases (in order)

| Step | Function | What It Does |
|---|---|---|
| 1 | `step_services()` | Checks Ollama + Docker; restarts missing containers |
| 2 | `step_review_logs()` | Reads recent repair logs, learning journal, mistakes file |
| 3 | `step_skill_discovery()` | Asks adwi:latest for 5 improvement suggestions → saves to pending-improvements.md |
| 3b | `step_aider_heal()` | Runs eval suite; if failing, invokes Aider up to 3 times; rolls back if still failing |
| 4 | `step_evals()` | Syntax check + routing eval |
| 5 | `step_system_health()` | brew outdated, npm outdated, disk usage, docker stats |
| 6 | `step_web_research()` | SearXNG queries for release notes on Ollama, Open WebUI, n8n, Qdrant |
| 7 | `step_memory_scan()` | Ingests terminal history, git commits, notes into memory.db |
| 8 | `step_capability_sync()` | Regenerates capabilities.json from adwi_cli.py |
| 9 | `step_git_commit()` | Commits and pushes all nightly changes |
| 10 | `step_obsidian_daily_note()` | Writes daily note to obsidian-vault/daily-notes/ |
| 11 | `step_write_report()` | Writes morning_brief.md to Desktop with Pending Approval section |

## Safety Constraints
- Never auto-applies package upgrades (written to Pending Approval section)
- Aider changes are rolled back via `git checkout -- .` if tests still fail after 3 attempts
- All writes go to designated sandbox paths only
- SearXNG search is read-only and local (no external tracking)
