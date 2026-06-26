# Decision: Bounded self-upgrade validation

- Idea ID: `20260625-232344-bounded-self-upgrade-validation`
- Decided: 2026-06-25T23:25:00.481281-05:00
- Status: accepted

## Decision

Adopt a bounded local-first self-upgrade loop: audit, profile, gap analysis, recommendations, research artifacts, MCP resource coverage, and health integration may refresh autonomously; external installs, private data indexing, communication sends, money actions, and destructive changes require explicit approval.

## Rationale

Local-first, inspectable, reversible changes are preferred unless the user explicitly approves broader integration.

## Follow-up

- Update implementation tasks if work remains.
- Update shared memory if this creates durable knowledge.
