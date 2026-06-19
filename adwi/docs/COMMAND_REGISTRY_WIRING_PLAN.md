# CommandRegistry Live Wiring Plan
*Design note — prepared 2026-06-19. Deferred until approved.*

---

## Current state

`adwi/adwi_cli.py` has two dispatch systems in parallel:

1. **`CommandRegistry`** — exists but is only used for `help` text generation (`.register()` decorates handlers with metadata). The live `handle()` method does NOT use the registry for dispatch.

2. **Legacy `elif` chain** — the actual dispatch. ~177 `elif cmd == "/..."` branches in `handle()`, plus NLU dispatch for non-slash inputs.

The registry collects: name, description, handler fn, args schema, risk level, examples. Nothing currently reads it at dispatch time.

---

## Goal

Wire `CommandRegistry` into live dispatch so slash commands route through a single place. This:
- Removes the 177-branch `elif` chain
- Makes each command's metadata (risk, args, help) authoritative at dispatch time
- Enables future: tab-completion, `/capabilities` auto-generation, fine-tuning export, CommandRegistry → `_INTENT_SYSTEM` sync

---

## Proposed approach

### Phase 1: Parallel dispatch (safe, no regression risk)

Add at the top of `handle()`:
```python
if text.startswith("/"):
    cmd_name = text.split()[0]
    handler = _registry.lookup(cmd_name)  # returns None if not registered
    if handler is not None:
        args = text[len(cmd_name):].strip()
        return handler(args)
    # fall through to legacy elif chain
```

This lets us migrate one command at a time without touching the elif chain. The elif chain is the authoritative fallback until all commands are migrated.

### Phase 2: Incremental migration (low-risk commands first)

Migrate in this order:
1. `/help`, `/status` — read-only, no side effects
2. `/memory-stats`, `/memory-context`, `/backup-status` — read-only
3. `/model-status`, `/capabilities`, `/eval-routing` — read-only
4. `/test-adwi`, `/syntax-check`, `/validate-docs` — test/read
5. Then write-path commands with explicit confirmation gate checks

Skip: `/gmail-*`, `/aider`, `/patch-adwi`, `/e2e-auto-loop` — leave in elif until well-tested

### Phase 3: Remove elif chain

Only after every command is registered AND parallel dispatch has run clean for ≥1 eval cycle.

---

## Files to touch

| File | Change |
|------|--------|
| `adwi/adwi_cli.py` | Add registry lookup at top of `handle()`; migrate commands one by one |
| `adwi/simlab/tests/test_nlu_regex.py` | Add test that all `/commands` in `handle()` have a registry entry |
| `adwi/docs/NLU_REPAIR_BACKLOG.md` | Note this as a wiring item (not NLU) |

---

## What NOT to do

- Don't create a separate `command_registry.py` file — `CommandRegistry` already exists in `adwi_cli.py`
- Don't change risk-tier logic or confirmation gates during migration
- Don't auto-generate `_INTENT_SYSTEM` from registry yet (future phase)
- Don't delete the elif chain until all commands are verified in parallel dispatch

---

## Acceptance criteria

- `adwi/.venv/bin/python3 adwi/adwi_cli.py /test-adwi` → 4/4
- `adwi/.venv/bin/python3 adwi/adwi_cli.py /eval-routing` → 30/30
- `adwi/.venv/bin/python3 -m pytest adwi/simlab/tests -q` → same count or more
- No change in NLU pass rate (registry dispatch is slash-only, NLU path unchanged)
