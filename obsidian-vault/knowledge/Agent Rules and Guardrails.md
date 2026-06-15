# Agent Rules & Guardrails

**Last Updated:** 2026-06-15
**Purpose:** Defines the operational boundaries for all autonomous Adwi agents and background routines.

---

## Core Principles

1. **Non-Destructive First** — No agent may delete, overwrite, or irreversibly modify files without first creating a timestamped backup.
2. **Sandbox Output** — All agent-generated artifacts go to designated directories (Desktop, obsidian-vault/logs/, notes/). No writes to system paths.
3. **Pending Approval Required** — Any dependency upgrade, new model download, or config change exceeding low-risk thresholds must be written to the "Pending User Approval" section of the morning brief. It must never be auto-applied.
4. **No Credential Transactions** — Browser automation (Playwright) is strictly read-only on sensitive domains. No form fills on banking, authentication, or external API management pages.
5. **Secrets Are Opaque** — `secrets/` and `config/.env` are read-only at agent startup. Contents are never logged, printed, or included in any brief or knowledge file.

---

## File Access Rules

### Allowed Read Roots (background agents)
- `~/SuneelWorkSpace/` (excluding `secrets/`)
- `~/SuneelWorkSpace/obsidian-vault/`
- `/tmp/` (ephemeral logs only)

### Hard-Blocked Paths (never read by any agent)
- `~/.ssh/`
- `~/.gnupg/`
- `~/Library/Keychains/`
- `~/Library/Passwords/`
- `~/.aws/`
- `~/.kube/`
- `~/SuneelWorkSpace/secrets/`
- `/etc/`, `/private/`, `/System/`

### Write Targets for Autonomous Agents
| Agent | May Write To |
|---|---|
| nightly.py | `notes/nightly-improvement-logs/`, `obsidian-vault/daily-notes/`, `~/Desktop/morning_brief.md` |
| overnight_learn.py | `adwi/knowledge.db`, `~/Desktop/morning_brief.md`, `/tmp/overnight-learn.log` |
| obsidian-bridge | `obsidian-vault/` (all subdirs) |
| adwi_cli.py | `notes/`, `open-webui-knowledge-upload/`, `adwi/memory.db` |

---

## Browser Automation (Playwright) Guardrails

**Allowed:**
- Navigate to public documentation sites
- Extract text and markdown from pages
- Screenshot pages for vision analysis
- Validate live information (release notes, status pages)

**Prohibited:**
- Fill or submit any form on domains involving authentication, payment, or credentials
- Execute JavaScript that modifies remote state
- Follow redirect chains more than 3 hops deep
- Store cookies or session tokens outside of the Playwright temp profile

---

## Nightly Loop Risk Classification

| Action | Risk | Auto-Execute? |
|---|---|---|
| Run evals / syntax check | None | Yes |
| Memory scan & indexing | None | Yes |
| Capability sync | Low | Yes |
| Git commit & push (known-good) | Low | Yes |
| Aider self-heal (rollback-safe) | Medium | Yes — rolls back on failure |
| Brew outdated check | None | Yes — report only |
| npm outdated check | None | Yes — report only |
| Apply patch version update | Medium | **No — Pending Approval** |
| Apply minor/major update | High | **No — Pending Approval** |
| Pull new Ollama model | Medium | **No — Pending Approval** |
| Modify system files | Critical | **Never** |

---

## Escalation Protocol

If a nightly agent encounters an error it cannot recover from:
1. Write a repair report to `~/Desktop/adwi-repair-report-YYYY-MM-DD.md`
2. Log the failure to `notes/adwi-repair-logs/`
3. Roll back any partial changes via `git checkout -- .`
4. Do not retry more than `MAX_FIX_ATTEMPTS` (currently 3)
5. Leave the system in its last-known-good state
