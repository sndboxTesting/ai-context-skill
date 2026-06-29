# dna

Identity profiles, Hermes agent, Ollama Modelfile, training data, and adapt loop.

## What It Does

- **Identity profiles** — Suneel's voice, tone, communication style, decision-making style
- **Hermes agent** — tirith-powered agent orchestrator built on Ollama
- **Ollama Modelfile** — `Modelfile.workspace` defines the `suneelworkspace` model (9,553-char system prompt)
- **Training data** — 103 training pairs extracted from workspace history for fine-tuning
- **Adapt loop** — scores and updates identity + communication style over time

## Identity Profiles

Load all 5 files when drafting, planning, or communicating on Suneel's behalf:

| File | Purpose |
|------|---------|
| `dna/identity/prompts/identity_prompt.md` | Prompt template for identity injection |
| `dna/identity/prompts/communication_prompt.md` | Communication style prompt |
| `dna/identity/profile/identity_profile.md` | Who Suneel is, goals, domain expertise |
| `dna/identity/profile/tone_profile.md` | Voice: short, direct, casual, conversational, smart, structured |
| `dna/identity/profile/decision_profile.md` | How Suneel makes decisions |

**Voice**: short, direct, casual, conversational, smart, structured, softened. Never harsh or condescending.

## Hermes Agent

```
dna/agents/hermes/
  ollama_models/
    Modelfile.workspace      # suneelworkspace model definition (9,553-char system prompt)
    build_modelfile.py       # Rebuilds Modelfile from live workspace state
    build_training_data.py   # Extracts training pairs from workspace history
    training_data.jsonl      # 103 training pairs (~41KB)
  skills/                    # Hermes skill definitions
  tools/                     # Hermes tool integrations
dna/feedback/                # Adapt loop feedback records
dna/identity/                # Identity + tone + decision profiles
```

## suneelworkspace Model

`Modelfile.workspace` builds `suneelworkspace` from `llama3.3:70b`:

```
FROM llama3.3:70b
SYSTEM """[9,553-char system prompt covering: Suneel's identity, all 12 organs,
           active tasks, decisions, patterns, operating rules, safety boundaries]"""
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1
```

Rebuild when workspace state changes significantly:

```bash
rebuild-model     # Regenerate Modelfile.workspace + run: ollama create suneelworkspace
```

## Training Data

`training_data.jsonl` — 103 pairs extracted by `build_training_data.py`:
- 100 git commit messages → what changed + why
- 3 repair loop suggestions → problem + fix
- Future: session logs, security findings

```bash
build-training-data    # Re-extract from current workspace history
```

## Context Injector Integration

Every Ollama engine call is enriched by `lab/autolab/context_injector.py` which injects 4,000 chars of live workspace state (identity_profile.md, tone_profile.md, MEMORY.md, ACTIVE_TASKS.md, SESSION_HANDOFF.md, DECISIONS.md, PATTERNS.md) as a system prompt. 5-minute TTL cache.

## CLI Commands

```bash
rebuild-model          # Rebuild suneelworkspace from live state
build-training-data    # Extract training pairs from workspace history
hermes-run             # Run Hermes agent
hermes-status          # Check Hermes + Ollama status
```

## Tests

Covered by `tests/organs/dna/test_dna.py` — part of the 103/103 passing suite.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("dna", "model_rebuilt", "dna/agents/hermes/ollama_models/Modelfile.workspace")
notify_change("dna", "training_data_updated", "dna/agents/hermes/ollama_models/training_data.jsonl")
```

*Updated: 2026-06-28*
