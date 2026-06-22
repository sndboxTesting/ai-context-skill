---
type: guide
status: active
tags: [workspace, organization, structure, meta]
updated: 2026-06-22
---

# Workspace Organization

How this workspace is structured, what belongs where, and how to start new work cleanly.

---

## Top-Level Repository Structure

| Folder | Purpose |
|--------|---------|
| `adwi/` | Main implemented project — AI OS source code, tests, evals, services |
| `obsidian-vault/` | Knowledge / ideas / planning layer (this vault) |
| `notes/` | Raw Adwi working notes and nightly improvement logs |
| `docs/` | Superpowers skill plugins |
| `logs/` | Runtime logs (NLU fast-path, system log) |
| `secrets/` | Credentials — **gitignored, never touch** |
| `.claude/` | Claude Code skills and session config |

**Rule:** Code goes into a named project folder (`adwi/`, or a new sibling like `home-hub/`). Notes, plans, and ideas go into `obsidian-vault/`. Nothing new at the top level unless it is a standalone project.

---

## Obsidian Vault Structure

```
obsidian-vault/
  Adwi Home.md              ← navigation hub
  System Map.canvas         ← visual system diagram
  daily-notes/              ← YYYY-MM-DD.md (auto-generated + manual captures)
  knowledge/                ← persistent reference docs, guides, maps
  projects/                 ← one folder per project; ideas subfolder
    Adwi.md
    ideas/                  ← one note per promoted idea
    life-automation/        ← non-Adwi life/work project brainstorms
  templates/                ← Obsidian templates (fill via Cmd+P)
  inbox/                    ← quick unprocessed captures (process weekly)
  automations/              ← n8n and Adwi automation reference docs
  logs/                     ← vault-level logs and archives
  reviews/                  ← weekly review notes (YYYY-MM-DD-weekly-review.md)
  prompts/                  ← reusable AI prompt fragments
  mcp-config/               ← MCP server configs
```

---

## Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Daily notes | `YYYY-MM-DD.md` | `2026-06-22.md` |
| Project note | `Title Case.md` | `Voice Input.md` |
| Weekly review | `YYYY-MM-DD-weekly-review.md` | `2026-06-22-weekly-review.md` |
| Idea brainstorm | `Title Case Brainstorm.md` | `Home Hub Brainstorm.md` |
| Implementation plan | `Title Case Plan.md` | `Voice Input Plan.md` |
| Project folder | `kebab-case/` | `life-automation/` |

---

## Idea-to-Implementation Lifecycle

```
1. Capture    → /obsidian-capture idea <text>
               → lands in daily note + Ideas Index

2. Brainstorm → create projects/ideas/<Title>.md using Idea Brainstorm template
               → flesh out the problem, approaches, score it

3. Prioritize → add to Master Ideas Index under the right tier
               → score on 6 criteria (see Ideas Operating System)

4. Promote    → /obsidian-promote-idea Title -- desc
               → creates a proper idea note; links from Ideas Index

5. Plan       → create implementation plan using Implementation Plan template
               → define MVP, milestones, risks, done criteria

6. Implement  → create a new code folder at workspace root (e.g., home-hub/)
               → use adwi/bin/ and adwi/ as reference patterns
               → link code folder from project note

7. Review     → use /obsidian-review-save to capture weekly progress
               → update Master Ideas Index status

8. Archive    → when complete or abandoned, move to Implemented / Rejected in Master Ideas Index
               → move code folder to obsidian-vault/logs/archive/<project>/ if abandoned
```

---

## How Adwi Fits This Model

`adwi/` is the only fully-implemented project. It is:
- **Active Project** in Master Ideas Index and Adwi Home
- Documented in `projects/Adwi.md` and `knowledge/` reference guides
- Operated via `obsidian-vault/` (daily notes, planning, reviews)
- Code lives at top-level `adwi/` — not inside obsidian-vault

---

## How to Start a New Non-Adwi Project

1. Capture the seed idea: `/obsidian-capture idea <text>`
2. Open `obsidian-vault/projects/life-automation/Life Automation Ideas.md` and add it under the right category.
3. When ready to brainstorm seriously: create `obsidian-vault/projects/ideas/<Title>.md` using the **Idea Brainstorm** template.
4. Score it. If ≥ 12 points (out of 25), promote it to Active.
5. Create an implementation plan using the **Implementation Plan** template.
6. Create a new code folder: `mkdir <project-name>/` at workspace root.
7. Link the code folder from your project note.
8. Build. Document decisions in daily notes.

---

## What NOT to Put Here

- No runtime databases (`*.db`, `*.db-shm`, `*.db-wal`) — gitignored
- No secret files — use `secrets/` which is gitignored
- No loose analysis files at the workspace root — use `adwi/docs/` or `obsidian-vault/knowledge/`
- No duplicate notes — one canonical location per topic

---

## Related Notes

- [[knowledge/Ideas Operating System]]
- [[knowledge/Master Ideas Index]]
- [[knowledge/Implementation Workflow]]
- [[projects/life-automation/Life Automation Ideas]]
- [[Adwi Home]]
