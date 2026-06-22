---
type: handoff
status: active
tags: [obsidian, handoff, upgrade, reference]
updated: 2026-06-22
---

# Obsidian Upgrade Handoff

Summary of what was built in the 2026-06-22 Obsidian upgrade session. Read this if you are resuming work on the vault integration or want to know what already exists before adding anything new.

**Do not add more Obsidian commands or nightly steps unless there is a concrete workflow gap you can name.**

---

## What Was Built

| Task | Outcome |
|------|---------|
| `/obsidian-plan-clear` semantics fix | Now blanks the `ADWI:DAILY-PLAN` block body to empty; `read_daily_plan()` returns `None` after clear |
| `clear_marker_block()` helper | Added to `obsidian_utils.py` — sets block body to `""`, no-op if marker absent |
| `/obsidian-status` | Prints vault summary + last nightly validation result from `adwi/logs/obsidian_last_validation.json` |
| Obsidian templates (6) | `Daily Note.md`, `Idea Note.md`, `Decision Record.md`, `Bug Fix Note.md`, `Project Note.md`, `Weekly Review.md` in `obsidian-vault/templates/` |
| `.obsidian/` vault config | `templates.json`, `daily-notes.json`, `core-plugins.json` committed; volatile files gitignored |
| `/obsidian-promote-idea` template reuse | Reads `templates/Idea Note.md` at runtime; inline fallback if file missing |
| `validate_obsidian_vault.py` | 8-check stdlib-only script: vault dirs, templates, `.obsidian` config, volatile files not tracked, Daily Note sync, Idea Note placeholders, knowledge docs, duplicate markers |
| `/obsidian-validate` | CLI wrapper — runs validator via subprocess, streams output |
| Nightly validation (step 12/14) | `step_obsidian_validate()` in `nightly.py`; persists result to `adwi/logs/obsidian_last_validation.json` |
| Nightly surface | Validation result appears in Home status block, Pending Approval (on failure), morning brief |
| `Obsidian Operator Guide.md` | Compact daily playbook — morning/day/weekly/health/where-things-live/markers |
| `/obsidian-help` | Prints `_OBSIDIAN_CHEAT_SHEET` — 8 commands + operator guide link |
| Cheat sheet in Adwi Home | `## Obsidian Command Cheat Sheet` section with 8 commands and operator guide link |
| `Template Guide.md` | Explains all 6 templates, placeholders, sync requirements |

---

## Command Surface (Obsidian)

| Command | What it does |
|---------|-------------|
| `/obsidian-status` | Vault summary: today's note, plan, last validation result |
| `/obsidian-plan [days]` | Generate daily plan from captures — writes `ADWI:DAILY-PLAN` block |
| `/obsidian-plan-clear` | Blank the `ADWI:DAILY-PLAN` block in today's note |
| `/obsidian-capture <type> <text>` | Append to today's daily note under matching section |
| `/obsidian-daily [entry]` | Quick-append to today's daily note |
| `/obsidian-review [days]` | Grouped summary of last N days of captures |
| `/obsidian-review-save [days]` | Save review to `reviews/YYYY-MM-DD-weekly-review.md` |
| `/obsidian-promote-idea Title -- desc` | Create idea note from template; link in Ideas Index |
| `/obsidian-read <path>` | Read a vault note by relative path |
| `/obsidian-write <path> -- <content>` | Append content to a vault note |
| `/obsidian-search <query>` | Full-text search across vault |
| `/obsidian-validate` | Run 8-check vault validator; exit 0 = all pass |
| `/obsidian-help` | Print command cheat sheet |

---

## Generated Marker Blocks

| Block | File | Written by |
|-------|------|------------|
| `ADWI:DAILY-SUMMARY` | `daily-notes/YYYY-MM-DD.md` | nightly (2 AM) |
| `ADWI:DAILY-BRIEF` | `daily-notes/YYYY-MM-DD.md` | `/daily-brief` |
| `ADWI:DAILY-PLAN` | `daily-notes/YYYY-MM-DD.md` | `/obsidian-plan` |
| `ADWI:HOME-STATUS` | `Adwi Home.md` | nightly (2 AM) |
| `ADWI:PENDING-APPROVAL` | `knowledge/Pending Approval.md` | nightly (2 AM) |
| `ADWI:REVIEW-CONTENT` | `reviews/YYYY-MM-DD-weekly-review.md` | `/obsidian-review-save` |

All markers use `replace_marker_block()` in `adwi/obsidian_utils.py`. Content inside is replaced in-place; content outside is never touched.

---

## Files and Directories Added

```
obsidian-vault/
  templates/
    Daily Note.md
    Idea Note.md
    Decision Record.md
    Bug Fix Note.md
    Project Note.md
    Weekly Review.md
  .obsidian/
    core-plugins.json     ← tracked
    templates.json        ← tracked
    daily-notes.json      ← tracked
    workspace.json        ← gitignored (volatile)
    workspace-mobile.json ← gitignored (volatile)
    graph.json            ← gitignored (volatile)
    app.json              ← gitignored (volatile)
    appearance.json       ← gitignored (volatile)
  knowledge/
    Obsidian Operator Guide.md
    Template Guide.md
    Obsidian Upgrade Handoff.md  ← this file

adwi/
  scripts/
    validate_obsidian_vault.py
  logs/
    obsidian_last_validation.json  ← gitignored (runtime state)

adwi/obsidian_utils.py    ← added clear_marker_block()
adwi/adwi_cli.py          ← added /obsidian-status, /obsidian-validate, /obsidian-help, plan-clear fix, promote-idea template reuse
adwi/nightly.py           ← added step 12/14 obsidian validation + surface in home/pending/brief
adwi/capabilities.json    ← added entries 173–175
adwi/tests/test_obsidian_utils.py  ← added TestClearMarkerBlock (5 tests), 56 total
```

---

## What Runs Nightly

Nightly loop (`adwi/nightly.py`, 2 AM):

| Step | What |
|------|------|
| 1 | Fetch latest commits |
| 2–8 | Git status, web research, AI suggestions, health checks |
| 9 | Gmail brief |
| 10 | Voice status |
| 11 | Write `ADWI:DAILY-SUMMARY` to today's daily note |
| **12/14** | **Obsidian vault validation** — runs `validate_obsidian_vault.py`; persists result to `adwi/logs/obsidian_last_validation.json` |
| 13/14 | Update `ADWI:HOME-STATUS` (Adwi Home) + `ADWI:PENDING-APPROVAL` (Pending Approval) — reads validation result from step 12 |
| 14/14 | Write morning report |

---

## Validation Command

```bash
python3 adwi/scripts/validate_obsidian_vault.py
# or from the Adwi REPL:
# /obsidian-validate
```

8 checks: vault dirs, all 6 templates present, `.obsidian` JSON config values, volatile files not tracked by git, Daily Note template section sync, Idea Note placeholders, 5 knowledge docs present, no duplicate markers in daily notes.

Exit 0 = all pass. Exit 1 = at least one fail (with `FAIL:` prefix lines).

---

## Known Non-Issues / Intentionally Ignored Files

| Item | Why it's fine |
|------|--------------|
| `.obsidian/workspace.json` etc. | Volatile UI state — gitignored by design; Obsidian regenerates them |
| `obsidian_last_validation.json` missing | Only exists after first nightly run; `/obsidian-status` shows "No validation record yet" |
| `adwi/memory.db`, `knowledge.db` | Gitignored runtime databases — regenerated on each machine |
| `notes/adwi-pending-improvements.md` dirty | Unrelated pre-existing changes — do not touch |
| `templates/` placeholders `{{date}}` etc. | Obsidian-native — filled by the Templates plugin; Adwi fills only `{{description}}` |

---

## Test Coverage

- `adwi/tests/test_obsidian_utils.py` — 56 tests (TestReplaceMarkerBlock, TestClearMarkerBlock, TestDailyNoteTemplate, TestTodayNotePath, TestDailyPlan, TestTimestampDedup, TestExtractSections, TestCollectDailyEntries)
- `adwi/simlab/tests/test_nlu_regex.py` — 481 tests, all pass (NLU baseline unchanged at 98.3%)
- No new NLU intents were added in this session

Run with:
```bash
python3 -m unittest adwi/tests/test_obsidian_utils.py
python3 -m unittest adwi/simlab/tests/test_nlu_regex.py
```

---

## Related Notes

- [[knowledge/Obsidian Operator Guide]]
- [[knowledge/Obsidian Maintenance]]
- [[knowledge/Template Guide]]
- [[knowledge/Workspace Organization]]
- [[knowledge/Master Ideas Index]]
- [[Adwi Home]]
