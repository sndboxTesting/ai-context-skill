---
type: guide
status: active
tags: [obsidian, daily, workflow, operator]
updated: 2026-06-22
---

# Obsidian Operator Guide

Day-to-day playbook — what to run and when.

For full detail see [[knowledge/Capture Workflow]], [[knowledge/Review Workflow]], [[knowledge/Planning Workflow]].

---

## Morning (2–3 min)

```bash
/obsidian-status        # today's note, plan, last nightly validation
/obsidian-plan 7        # generate today's plan from last 7 days of captures
/daily-brief            # priorities + plan pointer
```

---

## During the Day

Capture as things happen — takes 5 seconds each:

```bash
/obsidian-capture focus    finish the NLU regex audit
/obsidian-capture decision use stdlib-only in bridge to avoid deps
/obsidian-capture idea     auto-detect Ollama model on startup
/obsidian-capture bug      /daily-brief hangs when bridge is offline
/obsidian-capture fix      added timeout to _obsidian_api call
/obsidian-capture approval review brew upgrade for Python 3.14
/obsidian-capture note     researched marker-block pattern, works well
```

Each capture goes into today's daily note under the matching section.
`idea` also logs to `knowledge/Ideas Index.md`.
`approval` also logs to `knowledge/Pending Approval.md`.

---

## End of Day (5 min)

Open today's note in Obsidian (`Cmd+O` → type the date):
- Scan **Current Focus** — did everything get captured?
- Add any missed decisions or bugs manually.
- The `ADWI:DAILY-PLAN` block shows today's generated plan.

---

## Weekly (15 min)

```bash
/obsidian-review 7                                       # read what accumulated
/obsidian-review-save 7                                  # save to reviews/
/obsidian-promote-idea Rate Limiter Fix -- rewrite batch gmail fetch
```

Promote 1–3 ideas. Open the review note in Obsidian and add manual reflection.

---

## Health Check

```bash
/obsidian-validate   # structure, templates, config, markers
/obsidian-status     # quick summary + last nightly validation result
```

**If validation fails:**
1. Run `/obsidian-validate` — read the `FAIL:` lines
2. Fix manually (missing template file, corrupt marker, volatile `.obsidian` file tracked by git)
3. Re-run to confirm

Validation also runs automatically every night (step 12/14). Failures appear in:
- [[Adwi Home]] status block: `Obsidian vault: ✗ FAILED`
- [[knowledge/Pending Approval]]: pending item added

---

## Where Things Live

| Content | Path |
|---------|------|
| Daily notes | `daily-notes/YYYY-MM-DD.md` |
| Weekly reviews | `reviews/YYYY-MM-DD-weekly-review.md` |
| Idea notes | `projects/ideas/<Title>.md` |
| Templates | `templates/` (6 templates) |
| Ideas index | `knowledge/Ideas Index.md` |
| Pending approvals | `knowledge/Pending Approval.md` |
| Generated blocks | `<!-- ADWI:...:START/END -->` markers |

---

## Generated Marker Blocks

Adwi writes into notes using `<!-- ADWI:MARKER-NAME:START/END -->`. Content inside is replaced on each run; content outside is never touched.

| Block | Written to | Written by |
|-------|-----------|------------|
| `ADWI:DAILY-SUMMARY` | daily note | nightly 2 AM |
| `ADWI:DAILY-BRIEF` | daily note | `/daily-brief` |
| `ADWI:DAILY-PLAN` | daily note | `/obsidian-plan` |
| `ADWI:HOME-STATUS` | Adwi Home | nightly 2 AM |
| `ADWI:PENDING-APPROVAL` | Pending Approval | nightly 2 AM |
| `ADWI:REVIEW-CONTENT` | reviews/ | `/obsidian-review-save` |

---

## Related Notes

- [[knowledge/Capture Workflow]]
- [[knowledge/Review Workflow]]
- [[knowledge/Planning Workflow]]
- [[knowledge/Template Guide]]
- [[knowledge/Obsidian Maintenance]]
- [[knowledge/Obsidian Upgrade Handoff]]
- [[knowledge/Master Ideas Index]]
- [[knowledge/Ideas Operating System]]
- [[knowledge/Workspace Organization]]
- [[Adwi Home]]
