"""
Home Assistant MCP Server
Exposes Home Assistant REST API as MCP tools for Claude Code.
Run with: uv run --with mcp python3 server.py
Requires HOME_ASSISTANT_TOKEN and HOME_ASSISTANT_URL in config/.env
"""
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit("Run with: uv run --with mcp python3 server.py")

WORKSPACE = Path.home() / "SuneelWorkSpace"


def _load_env():
    env_path = WORKSPACE / "adwi" / "config" / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and v:
            os.environ.setdefault(k, v)


_load_env()
HA_URL   = os.environ.get("HOME_ASSISTANT_URL", "http://localhost:8123").rstrip("/")
HA_TOKEN = os.environ.get("HOME_ASSISTANT_TOKEN", "")

mcp = FastMCP("homeassistant")


def _ha_get(path: str) -> str:
    if not HA_TOKEN:
        return "HOME_ASSISTANT_TOKEN not set in config/.env"
    try:
        req = urllib.request.Request(
            f"{HA_URL}{path}",
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return f"Home Assistant offline ({HA_URL}): {e}"


def _ha_post(path: str, body: dict) -> str:
    if not HA_TOKEN:
        return "HOME_ASSISTANT_TOKEN not set in config/.env"
    try:
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            f"{HA_URL}{path}",
            data=data,
            headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode()
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return f"Home Assistant offline ({HA_URL}): {e}"


@mcp.tool()
def ha_status() -> str:
    """Check Home Assistant API status and version."""
    return _ha_get("/api/")


@mcp.tool()
def ha_get_state(entity_id: str) -> str:
    """Get the current state of a Home Assistant entity (e.g. 'light.living_room', 'sensor.temperature')."""
    return _ha_get(f"/api/states/{entity_id}")


@mcp.tool()
def ha_list_entities(domain: str = "") -> str:
    """List Home Assistant entities. Filter by domain (e.g. 'light', 'switch', 'sensor', 'climate'). Leave empty to list all."""
    raw = _ha_get("/api/states")
    try:
        states = json.loads(raw)
        if domain:
            states = [s for s in states if s.get("entity_id", "").startswith(f"{domain}.")]
        lines = []
        for s in sorted(states, key=lambda x: x.get("entity_id", "")):
            eid = s.get("entity_id", "")
            state = s.get("state", "")
            attrs = s.get("attributes", {})
            name = attrs.get("friendly_name", "")
            lines.append(f"{eid:<45} {state:<12} {name}")
        return "\n".join(lines) if lines else f"No entities found for domain '{domain}'"
    except json.JSONDecodeError:
        return raw


@mcp.tool()
def ha_call_service(domain: str, service: str, entity_id: str = "", data: str = "{}") -> str:
    """
    Call a Home Assistant service to control devices.
    Examples:
      domain='light' service='turn_on' entity_id='light.living_room'
      domain='light' service='turn_off' entity_id='light.all_lights'
      domain='climate' service='set_temperature' entity_id='climate.living_room' data='{"temperature": 22}'
      domain='switch' service='toggle' entity_id='switch.fan'
      domain='homeassistant' service='restart'
    """
    body = json.loads(data) if data and data != "{}" else {}
    if entity_id:
        body["entity_id"] = entity_id
    return _ha_post(f"/api/services/{domain}/{service}", body)


@mcp.tool()
def ha_get_lights() -> str:
    """Get all lights with their on/off state and brightness."""
    raw = _ha_get("/api/states")
    try:
        states = json.loads(raw)
        lights = [s for s in states if s.get("entity_id", "").startswith("light.")]
        lines = []
        for s in sorted(lights, key=lambda x: x.get("entity_id", "")):
            eid = s.get("entity_id", "")
            state = s.get("state", "")
            attrs = s.get("attributes", {})
            name = attrs.get("friendly_name", eid)
            brightness = attrs.get("brightness", "")
            brightness_pct = f" @ {int(brightness/255*100)}%" if brightness else ""
            lines.append(f"{'ON' if state == 'on' else 'off':<4} {name}{brightness_pct}")
        return "\n".join(lines) if lines else "No lights found"
    except json.JSONDecodeError:
        return raw


@mcp.tool()
def ha_get_sensors(keyword: str = "") -> str:
    """Get sensor readings (temperature, humidity, power, etc.). Filter by keyword in entity name."""
    raw = _ha_get("/api/states")
    try:
        states = json.loads(raw)
        sensors = [s for s in states if s.get("entity_id", "").startswith("sensor.")]
        if keyword:
            sensors = [s for s in sensors if keyword.lower() in s.get("entity_id", "").lower()
                       or keyword.lower() in s.get("attributes", {}).get("friendly_name", "").lower()]
        lines = []
        for s in sorted(sensors, key=lambda x: x.get("entity_id", "")):
            eid = s.get("entity_id", "")
            state = s.get("state", "")
            attrs = s.get("attributes", {})
            unit = attrs.get("unit_of_measurement", "")
            name = attrs.get("friendly_name", eid)
            lines.append(f"{name:<40} {state} {unit}")
        return "\n".join(lines) if lines else "No sensors found"
    except json.JSONDecodeError:
        return raw


@mcp.tool()
def ha_get_automations() -> str:
    """List all Home Assistant automations and their enabled/disabled state."""
    raw = _ha_get("/api/states")
    try:
        states = json.loads(raw)
        autos = [s for s in states if s.get("entity_id", "").startswith("automation.")]
        lines = []
        for s in sorted(autos, key=lambda x: x.get("entity_id", "")):
            eid = s.get("entity_id", "")
            state = s.get("state", "")
            name = s.get("attributes", {}).get("friendly_name", eid)
            lines.append(f"{'✓' if state == 'on' else '✗'} {name}")
        return "\n".join(lines) if lines else "No automations found"
    except json.JSONDecodeError:
        return raw


if __name__ == "__main__":
    mcp.run()
