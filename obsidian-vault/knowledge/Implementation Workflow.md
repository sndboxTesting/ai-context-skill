---
type: guide
status: active
tags: [implementation, workflow, development, projects]
updated: 2026-06-22
---

# Implementation Workflow

How to turn a planned idea into working software — cleanly, safely, without workspace clutter.

---

## When Is an Idea Ready to Build?

Before writing a line of code, verify:

- [ ] Brainstorm note exists in `projects/ideas/<Title>.md`
- [ ] Scored ≥ 20 on the Ideas OS scoring rubric
- [ ] Implementation Plan note filled in (MVP scope, milestones, done criteria)
- [ ] Privacy/safety risks evaluated — no hidden credential exposure
- [ ] Estimated time-to-MVP is clear (if it's >2 weeks, scope it down)

If any of these are missing, go back and fill them. Starting without a plan wastes implementation time.

---

## Creating a Project Folder

New project code lives at the workspace root, not inside `obsidian-vault/`:

```bash
mkdir <project-name>/
cd <project-name>/
git init  # or just start adding files — same git repo
```

Name it clearly in `kebab-case`: `home-hub/`, `email-digester/`, `finance-tracker/`.

Create a minimal structure:
```
<project-name>/
  README.md          ← what it is, how to run, how to test
  main.py            ← or index.ts, etc.
  requirements.txt   ← dependencies
  tests/
```

Link the folder from your project note in `obsidian-vault/projects/`.

---

## Building an MVP

**MVP rule:** the smallest thing that proves the idea works.

Steps:
1. Write the single-sentence outcome: "Given X, it does Y and produces Z."
2. Build only what produces Z — no UI polish, no edge-case handling, no configurability.
3. Manually test the golden path once.
4. Capture what you learned via `/obsidian-capture decision <text>`.

If the MVP doesn't work after a week, the idea may need re-scoping or rejecting.

---

## Documenting Decisions

All decisions go into daily notes via Adwi:

```bash
/obsidian-capture decision chose sqlite over postgres — no network dep needed
/obsidian-capture decision dropped oauth2 flow — out of scope for MVP
```

Major architectural decisions go into a Decision Record note using the **Decision Record** template:
`Cmd+P → Templates: Insert template → Decision Record`

Keep decision notes in `obsidian-vault/projects/ideas/` or a project subfolder in `knowledge/`.

---

## Using Adwi / Codex / Claude Safely

**Adwi (local model):**
- Use for code generation, debugging, research
- `/research <question>` for multi-source research
- Never ask it to read `secrets/`, `.env`, or `~/.ssh/`

**Claude Code (this session):**
- Safe for file edits, refactoring, test writing
- Do not paste credential values into the conversation
- PathValidator blocks dangerous paths at execution layer

**Codex (via MCP):**
- Reviewer role only (`read-only`, `approval-policy: never`)
- Use via `/codex-advisor` skill — never give it write access
- Do not send credential file contents in the review brief

---

## Avoiding Clutter

| Rule | Why |
|------|-----|
| One project folder per project | No flat files at workspace root |
| No loose analysis files at root | Use `adwi/docs/` or `obsidian-vault/knowledge/` |
| No runtime artifacts in git | Add to `.gitignore` before first commit |
| No `print`-debugging left in code | Clean before committing |
| Max 1 brainstorm + 1 plan note per idea | More notes = more maintenance burden |

---

## Reviewing and Archiving

**When it's done:**
1. Update [[knowledge/Master Ideas Index]] → move to Implemented
2. Write a short retrospective in `obsidian-vault/reviews/` (`/obsidian-review-save`)
3. Tag the final commit with `v1.0` or `done`

**When it's abandoned:**
1. Update Master Ideas Index → move to Rejected/Parked with a reason
2. Move or archive the code folder only if it's truly dead weight
3. Keep the brainstorm and plan notes in `projects/ideas/` — they're cheap to keep and may be useful later

**When it evolves into something bigger:**
1. Create a new project folder (the old one becomes a prototype)
2. Create a new project note in `projects/`
3. Link the prototype from the new note as prior art

---

## Related Notes

- [[knowledge/Ideas Operating System]]
- [[knowledge/Workspace Organization]]
- [[knowledge/Master Ideas Index]]
- [[knowledge/Capture Workflow]]
- [[knowledge/Planning Workflow]]
- [[Adwi Home]]
