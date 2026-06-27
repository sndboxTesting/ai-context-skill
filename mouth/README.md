# 👄 Mouth — SuneelWorkSpace Organ

## Purpose
Interprets user requests and routes comms via Mail or iMessage.

## What\s Inside
* `dispatcher/`: classifier intents parser ws.py.
* `comms/`: messaging helper utilities.

## Key Files
* [mouth/dispatcher/ws.py](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/ws.py): NL command interpreter hook.
* [mouth/dispatcher/intent_map.json](file:///Users/MAC/SuneelWorkSpace/mouth/dispatcher/intent_map.json): Intent command map.
* [mouth/comms/mail/scripts/mail-recent](file:///Users/MAC/SuneelWorkSpace/mouth/comms/mail/scripts/mail-recent): Mail list fetcher.

## Provides (to other organs)
* Command classification mappings and communication links.

## Needs (from other organs)
* Vector search memory matching from `brain`.
* Goal statuses from `heart`.

## CLI Commands
* `ws`: NL command dispatcher.
* `mail-status`: outbound email status.
* `imessage-status`: iMessage permissions and delivery.

## How To Add Something Here
1. Put new intents in `dispatcher/intent_map.json`.
2. Add mailing integrations under `comms/`.
