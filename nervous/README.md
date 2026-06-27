# 🫀 Nervous — SuneelWorkSpace Organ

## Purpose
Coordinates event-driven nerve propagation, REST API gateways, and MCP servers.

## What\s Inside
* `gateway/`: Gateway client wrappers.
* `mcp/`: Model Context Protocol server modules.
* `skills/`: Specialist system prompts and tool policies.

## Key Files
* [nervous/nerve_propagator.py](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_propagator.py): Central communication router.
* [nervous/nerve_registry.json](file:///Users/MAC/SuneelWorkSpace/nervous/nerve_registry.json): Organ connection maps.
* [nervous/mcp/server/main.py](file:///Users/MAC/SuneelWorkSpace/nervous/mcp/server/main.py): Exposes filesystem, search, and system connector APIs.

## Provides (to other organs)
* Event notifications.
* Gateway REST endpoints.
* Model Context Protocol resources.

## Needs (from other organs)
* Subsystem file listings from `spine`.
* Global boundaries from `skeleton`.

## CLI Commands
* `nerve-status`: Checks notifications states.
* `mcp-start`: Launches MCP server.
* `mcp-status`: Gateway connection verification.
* `mcp-doctor`: Pings server diagnostics.
* `mcp-reindex`: Re-indexes MCP assets.

## How To Add Something Here
1. Add new subscribers to `nerve_registry.json`.
2. Register resource links inside `nervous/mcp/server/config/resource_map.json`.
