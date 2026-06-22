---
type: guide
status: active
tags: [obsidian, templates, workflow]
updated: 2026-06-22
---

# Template Guide

How to use Obsidian templates in this vault — and how they relate to Adwi commands.

---

## Templates Available

All templates live in `obsidian-vault/templates/`.

| Template | Use when | Adwi equivalent |
|----------|----------|-----------------|
| `Daily Note.md` | Obsidian creates today's note | `/daily-brief`, nightly |
| `Idea Note.md` | You want a full project note for an idea | `/obsidian-promote-idea` |
| `Decision Record.md` | You made a significant architectural decision | `/obsidian-capture decision` (quick), manual (detailed) |
| `Bug Fix Note.md` | You want a dedicated note for a bug | `/obsidian-capture bug/fix` (quick), manual (detailed) |
| `Project Note.md` | You're starting a new project or major feature | manual (no Adwi command) |
| `Weekly Review.md` | You want a manual review note | `/obsidian-review-save` (generated), manual (this template) |

---

## How to Use Templates from Obsidian

1. Open the Obsidian command palette (`Cmd+P`)
2. Search for **"Templates: Insert template"**
3. Select the template you want
4. Obsidian fills in `{{title}}` (from the note filename), `{{date}}`, `{{time}}`

For daily notes, Obsidian auto-applies `templates/Daily Note.md` when you open a new day from the calendar — configured in `Settings → Core plugins → Daily notes`.

---

## Template Placeholders

Standard Obsidian placeholders (filled automatically by Obsidian's Templates plugin):

| Placeholder | Filled with |
|-------------|-------------|
| `{{title}}` | Current note filename (without `.md`) |
| `{{date}}` | Today's date in `YYYY-MM-DD` format |
| `{{date:YYYY-MM-DD}}` | Today's date, explicit format |
| `{{time}}` | Current time `HH:mm` |

Custom placeholders used only by Adwi's `/obsidian-promote-idea`:

| Placeholder | Filled with |
|-------------|-------------|
| `{{description}}` | The `-- <description>` argument you provide |

Obsidian does **not** fill `{{description}}` — only Adwi does.

---

## How Templates Relate to Adwi Commands

### Daily notes
- **Obsidian** creates `daily-notes/YYYY-MM-DD.md` using `templates/Daily Note.md` when you open a new day.
- **Adwi nightly** creates the same file at 2 AM if absent (using `obsidian_utils.daily_note_template()`).
- **Both produce the same section structure** — the template and the `daily_note_template()` function are kept in sync manually.
- Generated `ADWI:DAILY-SUMMARY` and `ADWI:DAILY-BRIEF` marker blocks are appended by Adwi; they are NOT in the template.

### Idea notes
- `/obsidian-promote-idea <Title> -- <description>` reads `templates/Idea Note.md`, fills `{{title}}`, `{{description}}`, `{{date}}`, and writes to `projects/ideas/<Title>.md`.
- If the template file is missing, the command falls back to an inline default.

### Weekly reviews
- `/obsidian-review-save` writes a generated `ADWI:REVIEW-CONTENT` marker block to `reviews/YYYY-MM-DD-weekly-review.md`. It does **not** use `templates/Weekly Review.md`.
- Use `templates/Weekly Review.md` if you want to start a manual review note with a consistent structure before running `/obsidian-review-save`.

---

## Keeping Templates and Adwi in Sync

If you change the section headings in `templates/Daily Note.md`, also update:
- `adwi/obsidian_utils.py` → `_TEMPLATE` constant and `REVIEW_SECTIONS` list
- `adwi/adwi_cli.py` → `_CAPTURE_SECTIONS` dict

If you change `templates/Idea Note.md` headings, the `/obsidian-promote-idea` command may fail to find `## Captured Updates` for appending. Keep that heading in the file.

---

## TODO

- `/obsidian-promote-idea` could eventually read `Decision Record.md` for a `/obsidian-promote-decision` command.
- `Bug Fix Note.md` could link into a future `/obsidian-promote-bug` command.

---

## Related Notes

- [[knowledge/Capture Workflow]]
- [[knowledge/Review Workflow]]
- [[knowledge/Planning Workflow]]
- [[knowledge/Obsidian Maintenance]]
- [[Adwi Home]]
