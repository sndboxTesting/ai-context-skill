---
type: guide
status: active
tags: [obsidian, review, workflow, weekly]
updated: 2026-06-22
---

# Review Workflow

How to turn captured items into promoted, actionable knowledge — so your daily notes don't just accumulate.

---

## The Three-Step Loop

```
Capture   →   Review   →   Promote
(daily)       (weekly)     (on demand)
```

1. **Capture** daily with `/obsidian-capture <type> <text>` — goes into today's daily note.
2. **Review** at end of week with `/obsidian-review` — see what accumulated.
3. **Promote** good ideas with `/obsidian-promote-idea` — turns a bullet into a real project note.

---

## Commands

### `/obsidian-review [days]`  *(read-only)*

```bash
/obsidian-review         # last 7 days
/obsidian-review 14      # last 14 days
```

Reads the last N daily notes and prints a grouped summary:

| Section | What you see |
|---------|-------------|
| Focus / Tasks | All focus + task captures |
| Decisions | Decision log entries |
| Ideas to Promote | Ideas worth acting on |
| Bugs / Fixes | Recorded bugs and fixes |
| Pending Approval | Items waiting for human review |
| Notes | Miscellaneous notes |

Each entry shows its source date. Nothing is written — safe to run anytime.

---

### `/obsidian-review-save [days]`

```bash
/obsidian-review-save        # last 7 days
/obsidian-review-save 14     # last 14 days
```

Saves a structured review note to:
```
obsidian-vault/reviews/YYYY-MM-DD-weekly-review.md
```

- First run: creates the note with frontmatter and a source-note list.
- Re-run on the same day: updates the `<!-- ADWI:REVIEW-CONTENT:START/END -->` block in-place. Manual edits outside the block are preserved.

**Suggested weekly habit:** Run `/obsidian-review-save` every Sunday. Open the note in Obsidian, review the ideas section, and promote the best ones.

---

### `/obsidian-promote-idea <Title> -- <description>`

```bash
/obsidian-promote-idea Auto-Classify Screenshots -- classify desktop screenshots and route to relevant projects automatically
```

Creates:
```
obsidian-vault/projects/ideas/<Title>.md
```

The note uses the standard idea template (same as existing idea notes):
- frontmatter (`type: idea`, `status: planned`)
- `## Status`, `## Why It Matters`, `## Existing Related Files`
- `## Implementation Sketch`, `## Risks`, `## Next Action`
- `## Related Notes`

Also inserts a row in `knowledge/Ideas Index.md → ## Active Ideas` table if not already present.

**If the note already exists:** appends a `## Captured Updates` entry with the date and description instead of overwriting.

---

## Typical Weekly Session (15 min)

```bash
# 1. See what was captured this week
/obsidian-review 7

# 2. Save a review note
/obsidian-review-save 7

# 3. Promote the best idea
/obsidian-promote-idea My Best Idea This Week -- why it matters and what to build

# 4. Open the review note in Obsidian to add manual notes
```

---

## Where Things Live

| Output | Path |
|--------|------|
| Daily captures | `obsidian-vault/daily-notes/YYYY-MM-DD.md` |
| Weekly review notes | `obsidian-vault/reviews/YYYY-MM-DD-weekly-review.md` |
| Promoted idea notes | `obsidian-vault/projects/ideas/<Title>.md` |
| Idea index | `obsidian-vault/knowledge/Ideas Index.md` |
| Pending approvals | `obsidian-vault/knowledge/Pending Approval.md` |

---

## Related Notes

- [[knowledge/Planning Workflow]]
- [[knowledge/Capture Workflow]]
- [[knowledge/Template Guide]]
- [[knowledge/Obsidian Maintenance]]
- [[knowledge/Ideas Index]]
- [[knowledge/Pending Approval]]
- [[Adwi Home]]
