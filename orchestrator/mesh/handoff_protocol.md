# Multi-Agent Handoff Protocol

Every agent MUST write this block at session close into `SESSION_HANDOFF.md` and `SESSION_HANDOFF.json`.

## Handoff Block (Machine-Readable)

```json
{
  "session_id": "<uuid>",
  "agent": "claude|codex|gemini|opencode|antigravity",
  "intent": "<what was being worked on>",
  "completed_tasks": [],
  "open_tasks": [],
  "decisions_made": [],
  "files_modified": [],
  "suggested_next_agent": "<agent name>",
  "suggested_next_action": "<next thing to do>",
  "context_snapshot": "<one paragraph summary>"
}
```

## Rules

- `session_id`: use a short timestamp or uuid
- `agent`: must be one of the registered agents in `agent_registry.json`
- `completed_tasks`: list of task IDs or descriptions finished this session
- `open_tasks`: list of task IDs or descriptions left open
- `decisions_made`: key decisions with brief rationale
- `files_modified`: list of paths changed (relative to workspace root)
- `suggested_next_agent`: which agent should pick this up next
- `suggested_next_action`: exact first action the next agent should take
- `context_snapshot`: human-readable summary (1 paragraph max)

## Format Rules

- Write JSON block at top of `SESSION_HANDOFF.md` under `## Machine-Readable Handoff`
- Write human prose below under `## Human Summary`
- Also write full JSON to `SESSION_HANDOFF.json`
- Both formats are updated by `agent-finish`

## Agent Selection Guide

| Task Type          | Best Agent      |
|--------------------|-----------------|
| Deep coding        | claude          |
| Shell automation   | codex           |
| Long research      | gemini          |
| Fast batch tasks   | opencode        |
| Orchestration/MCP  | antigravity     |
