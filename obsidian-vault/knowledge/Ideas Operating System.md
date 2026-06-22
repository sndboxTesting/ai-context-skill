---
type: guide
status: active
tags: [ideas, workflow, prioritization, brainstorm]
updated: 2026-06-22
---

# Ideas Operating System

A personal system for moving ideas from raw capture to built reality — without losing them or drowning in them.

---

## 1. Capture (30 seconds)

The rule: **capture immediately, process later.**

```bash
/obsidian-capture idea <text>       # from Adwi REPL
```

Or drop it in `obsidian-vault/inbox/` as a quick note. Process inbox weekly.

Every captured idea lands in:
- Today's daily note under `## Ideas`
- `knowledge/Ideas Index.md` under "Captured Ideas"

---

## 2. Brainstorm (30–60 min)

When an idea keeps coming back, create a brainstorm note:

1. Create `obsidian-vault/projects/ideas/<Title>.md` using the **Idea Brainstorm** template (`Cmd+P → Templates: Insert template → Idea Brainstorm`).
2. Fill in: the problem it solves, who benefits, 2–3 approaches, quick score.
3. List what you'd need to know before starting.

**Don't over-engineer.** A brainstorm note is a thinking tool, not a spec.

---

## 3. Score and Prioritize

Rate each idea on 6 criteria (1–5 each, lower = better on cost/risk dimensions):

| Criterion | 1 (best) | 5 (worst) | Notes |
|-----------|---------|---------|-------|
| **Daily-life usefulness** | Changes daily behavior | Nice to have | How often would you use it? |
| **Implementation difficulty** | Weekend project | Multi-month deep work | Estimate lines of code, new skills needed |
| **Automation potential** | Fully automated | Manual every time | Can Adwi/n8n drive it? |
| **Privacy/safety risk** | Zero exposure | Touches credentials/data | Does it need secrets, cloud APIs, personal data? |
| **Dependency cost** | Zero new deps | Heavy new infra | New services, subscriptions, hardware? |
| **Time-to-first-working-version** | 1–2 days | 1+ months | Raw estimate |

**Scoring (usefulness + automation are inverted — higher is better):**

```
Score = usefulness×2 + automation×2 + (6 - difficulty) + (6 - risk) + (6 - deps)
```

Max = 40. Rough tiers:
- **30–40** → strong candidate, build soon
- **20–29** → worth planning, no rush
- **10–19** → interesting but not now
- **<10** → park in Someday/Maybe or reject

Add the score to [[knowledge/Master Ideas Index]].

---

## 4. Promote

When an idea scores ≥ 20 and you have bandwidth:

```bash
/obsidian-promote-idea "Title" -- one-line description
```

This creates `obsidian-vault/projects/ideas/<Title>.md` using the Idea Note template and links it from the Ideas Index.

Move the idea from "Raw" to "Promoted" in [[knowledge/Master Ideas Index]].

---

## 5. Create an Implementation Plan

Before writing code, fill in the **Implementation Plan** template:

1. Create `obsidian-vault/projects/ideas/<Title> Plan.md`
2. Use `Cmd+P → Templates: Insert template → Implementation Plan`
3. Define: MVP scope, milestones, risks, done criteria, tools
4. Time-box: commit to a start date and a "stop-and-review" date

**The plan is not a contract — it is a forcing function.** Update it as you learn.

---

## 6. Implement

See [[knowledge/Implementation Workflow]] for the full guide. Short version:

1. Create a code folder at workspace root: `mkdir <project>/`
2. Build the MVP first — nothing else counts
3. Capture decisions in daily notes via `/obsidian-capture decision <text>`
4. Capture bugs in daily notes via `/obsidian-capture bug <text>`
5. Link commits to the project note manually when useful

---

## 7. Track Progress

- **Daily:** capture any decisions, fixes, or blockers via `/obsidian-capture`
- **Weekly:** run `/obsidian-review 7` to see what accumulated; update Master Ideas Index status
- **On milestone:** save a review note via `/obsidian-review-save`

---

## 8. Review and Archive

At the weekly review:
1. Check [[knowledge/Master Ideas Index]] — move anything that's done to **Implemented**
2. Move anything stalled >4 weeks to **Parked**
3. Promote 1–2 raw ideas if bandwidth allows
4. Delete or reject ideas that no longer seem worth tracking

---

## Anti-Patterns to Avoid

| Anti-pattern | What to do instead |
|-------------|--------------------|
| Capturing ideas but never processing them | Weekly review: process inbox + Raw → Promoted |
| Starting implementation before an MVP plan exists | Fill Implementation Plan template first |
| Building too much before testing it | Stop at the smallest thing that proves the idea works |
| Keeping everything in "Active" forever | Move stalled work to Parked; clear the list |
| Creating too many notes per idea | One brainstorm note + one plan note per idea, max |

---

## Related Notes

- [[knowledge/Master Ideas Index]]
- [[knowledge/Workspace Organization]]
- [[knowledge/Implementation Workflow]]
- [[projects/life-automation/Life Automation Ideas]]
- [[knowledge/Capture Workflow]]
- [[knowledge/Review Workflow]]
- [[knowledge/Planning Workflow]]
