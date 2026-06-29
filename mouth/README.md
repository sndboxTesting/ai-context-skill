# mouth

Intent dispatcher, communication channel adapters (mail, iMessage), and outbound message routing.

## What It Does

- **Intent dispatcher** (`mouth/ws.py`) — receives intents, routes to the right channel
- **Intent map** — `mouth/intent_map.json` defines 9+ intent→handler mappings
- **Mail adapter** — `mouth/comms/mail.py` sends email via Gmail
- **iMessage adapter** — `mouth/comms/imessage.py` sends iMessages (macOS only)
- **SAFETY**: all outbound communication requires explicit human approval before sending

## Key Files

| File | Purpose |
|------|---------|
| `mouth/ws.py` | Intent dispatcher — routes intents to channels |
| `mouth/intent_map.json` | Intent name → handler + channel mapping (9 intents) |
| `mouth/comms/mail.py` | Gmail email adapter |
| `mouth/comms/imessage.py` | iMessage adapter |
| `mouth/dispatcher/` | Dispatcher core logic |
| `mouth/nerve.json` | Organ manifest v1.1 |

## Intent Map

`intent_map.json` defines how incoming intents route to channels:

| Intent | Channel | Notes |
|--------|---------|-------|
| `send_email` | mail | Requires approval |
| `send_imessage` | iMessage | Requires approval |
| `morning_brief` | mail | Built by ears/digest_builder |
| `alert` | iMessage | High-priority |
| + 5 more | varies | See intent_map.json |

## Safety Boundary

**Never send outbound comms without explicit approval.** This organ is `HUMAN_REQUIRED` per `skeleton/rules/SAFETY_BOUNDARIES.md`.

The dispatcher must check the Approval Queue (dashboard widget or `blood/logs/suggestion_controlled_queue.json`) before executing any send action.

## CLI Commands

```bash
mouth-dispatch "intent"  # Dispatch an intent through the router
mouth-status             # Check channel adapter health
```

## Tests

Covered by `tests/organs/mouth/test_mouth.py` — part of the 103/103 passing suite.

## Nerve Events

```python
from nervous.nerve_propagator import notify_change
notify_change("mouth", "message_sent", "mouth/comms/")
notify_change("mouth", "intent_dispatched", "mouth/ws.py")
```

*Updated: 2026-06-28*
