---
type: guide
status: active
tags: [obsidian, capture, daily-notes, workflow]
updated: 2026-06-21
---

# Capture Workflow

How to quickly log thoughts, decisions, and bugs into your Obsidian vault from the Adwi REPL.

---

## Command

```
/obsidian-capture <type> <text>
```

Appends a `- HH:MM — text` entry to the matching section of **today's daily note**.
Works even when the Obsidian Bridge is offline — writes directly to the vault file.

---

## Types and Their Targets

| Type | Daily note section | Extra index |
|------|--------------------|-------------|
| `focus` | `## Current Focus` | — |
| `task` | `## Current Focus` | — |
| `decision` | `## Decisions` | — |
| `idea` | `## Ideas` | `knowledge/Ideas Index.md` → `## Captured Ideas` |
| `bug` | `## Bugs / Fixes` | — |
| `fix` | `## Bugs / Fixes` | — |
| `approval` | `## Pending Approval` | `knowledge/Pending Approval.md` → `## Manual Pending Items` |
| `note` | `## Notes` | — |

---

## Examples

```bash
/obsidian-capture focus finish the NLU regex audit
/obsidian-capture decision use stdlib-only in bridge to avoid deps
/obsidian-capture idea auto-detect Ollama model version on startup
/obsidian-capture bug /daily-brief hangs when bridge is offline
/obsidian-capture fix added timeout to _obsidian_api call
/obsidian-capture approval review Brew upgrade for Python 3.14
/obsidian-capture note researched marker-block pattern, works well
```

---

## Behaviour

- **No duplicates** — if the exact entry already exists under that heading, the write is skipped.
- **Section creation** — if a section like `## Notes` is absent, it is appended at the end of the note.
- **Marker-safe** — entries are never inserted inside `<!-- ADWI:...:START/END -->` generated blocks.
- **Index updates** — `idea` and `approval` types also append to their respective index files.

---

## Related Notes

- [[knowledge/Review Workflow]]
- [[knowledge/Planning Workflow]]
- [[Adwi Home]]
- [[knowledge/Obsidian Maintenance]]
- [[knowledge/Ideas Index]]
- [[knowledge/Pending Approval]]
- [adwi/obsidian_utils.py](../../adwi/obsidian_utils.py)
