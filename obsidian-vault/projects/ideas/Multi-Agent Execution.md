---
type: idea
status: planned
tags: [idea, roadmap, agents, parallel]
updated: 2026-06-21
---

# Multi-Agent Execution

#idea #roadmap #agents

## Status
🔵 Planned — not started

## Why It Matters
Adwi currently runs all tasks sequentially in a single REPL. Multi-agent execution lets it spawn sub-agents for parallel research and implementation — e.g., researching a library while simultaneously drafting an implementation plan, then combining results.

## Existing Related Files

| File | Relevance |
|------|-----------|
| `adwi/reason_engine.py` | LangGraph Planner→Executor→Critic — spawn point |
| `adwi/adwi_cli.py` | `/reason` command triggers `run_reason()` |
| `adwi/simlab/` | Already uses subprocess-based parallel eval workers |
| `adwi/services/command-api/server.py` | E2E loop uses Popen for background execution |

## Implementation Sketch

1. Add `SubAgentRunner` to `reason_engine.py` — wraps a `reason_engine.run_reason()` call in a subprocess/thread
2. PlannerAgent identifies parallelizable steps (no `depends_on` edges)
3. Spawn sub-agents for independent steps, collect results via queue
4. CriticAgent synthesizes combined output
5. Achievement ledger tracks per-agent contributions

Constraint: PathValidator and BLOCKED_PATHS must be enforced in each sub-agent process. Sub-agents must not share mutable state.

## Risks

- Ollama concurrency: adwi:latest is 18.6 GB — parallel 30B model calls may saturate RAM
- Safe approach: use lighter models (llama3.1:8b) for sub-agents, reserve adwi:latest for synthesis
- Deadlock: sub-agents waiting on each other must timeout
- Permission gates: REVIEW-REQUIRED steps cannot be parallelized — must be sequential

## Next Action

Audit `reason_engine.py` for state that would be unsafe to share across processes. Design the SubAgentRunner interface.

## Related Notes

- [[projects/ideas/Implement from Video]]
- [[knowledge/Automation Map]]
- [[knowledge/Ideas Index]]
- [adwi/reason_engine.py](../../../adwi/reason_engine.py)
