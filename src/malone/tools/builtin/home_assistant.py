from __future__ import annotations

import json

import httpx

from malone.config.settings import get_settings
from malone.tools.base import BaseTool


def _get_ha_config():
    """Get Home Assistant config (URL and token)."""
    settings = get_settings()
    return settings.home_assistant


class HAListEntitiesTool(BaseTool):
    """Lists available Home Assistant entities."""

    @property
    def name(self) -> str:
        return "ha_list_entities"

    @property
    def description(self) -> str:
        return (
            "List available Home Assistant entities (devices). "
            "Optionally filter by domain (light, switch, climate, sensor, etc). "
            "Returns entity_id, friendly name, and current state."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "Filter by entity domain: light, switch, climate, sensor, "
                        "binary_sensor, media_player, automation, scene, cover, fan, lock. "
                        "Leave empty to list all."
                    ),
                },
            },
            "required": [],
        }

    async def execute(self, domain: str = "") -> str:
        config = _get_ha_config()
        if not config.url or not config.token.get_secret_value():
            return "Error: Home Assistant not configured. Set MALONE_HOME_ASSISTANT__URL and MALONE_HOME_ASSISTANT__TOKEN."

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{config.url}/api/states",
                headers={"Authorization": f"Bearer {config.token.get_secret_value()}"},
            )
            resp.raise_for_status()
            states = resp.json()

        if domain:
            states = [s for s in states if s["entity_id"].startswith(f"{domain}.")]

        results = []
        for entity in states[:50]:  # Limit to avoid flooding
            name = entity.get("attributes", {}).get("friendly_name", "")
            results.append(
                f"  {entity['entity_id']}: {entity['state']} ({name})"
            )

        if not results:
            return f"No entities found{' for domain ' + domain if domain else ''}."
        return f"Found {len(results)} entities:\n" + "\n".join(results)


class HAControlDeviceTool(BaseTool):
    """Controls a Home Assistant device."""

    @property
    def name(self) -> str:
        return "ha_control_device"

    @property
    def description(self) -> str:
        return (
            "Control a Home Assistant device. Supports turning on/off lights, "
            "switches, fans, covers, locks, and setting climate temperature. "
            "Use ha_list_entities first to discover available entity IDs."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The entity ID to control (e.g. 'light.living_room')",
                },
                "action": {
                    "type": "string",
                    "description": (
                        "Action to perform: 'turn_on', 'turn_off', 'toggle', "
                        "'set_temperature', 'set_brightness'"
                    ),
                },
                "value": {
                    "type": "string",
                    "description": (
                        "Optional value for the action: temperature in F/C, "
                        "brightness 0-255, or color name."
                    ),
                },
            },
            "required": ["entity_id", "action"],
        }

    async def execute(self, entity_id: str, action: str, value: str = "") -> str:
        config = _get_ha_config()
        if not config.url or not config.token.get_secret_value():
            return "Error: Home Assistant not configured."

        domain = entity_id.split(".")[0]
        headers = {"Authorization": f"Bearer {config.token.get_secret_value()}"}

        # Build the service call
        service_data: dict = {"entity_id": entity_id}

        if action == "set_temperature" and value:
            service = "climate/set_temperature"
            service_data["temperature"] = float(value)
        elif action == "set_brightness" and value:
            service = f"{domain}/turn_on"
            service_data["brightness"] = int(value)
        elif action in ("turn_on", "turn_off", "toggle"):
            service = f"{domain}/{action}"
        else:
            return f"Unknown action '{action}'. Use: turn_on, turn_off, toggle, set_temperature, set_brightness."

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{config.url}/api/services/{service}",
                headers=headers,
                json=service_data,
            )
            resp.raise_for_status()

        return f"OK: {action} on {entity_id}" + (f" (value: {value})" if value else "")


class HATriggerSceneTool(BaseTool):
    """Triggers a Home Assistant scene or automation."""

    @property
    def name(self) -> str:
        return "ha_trigger_scene"

    @property
    def description(self) -> str:
        return (
            "Trigger a Home Assistant scene or automation. "
            "Use ha_list_entities with domain 'scene' or 'automation' to find available ones."
        )

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The scene or automation entity_id (e.g. 'scene.movie_night')",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, entity_id: str) -> str:
        config = _get_ha_config()
        if not config.url or not config.token.get_secret_value():
            return "Error: Home Assistant not configured."

        headers = {"Authorization": f"Bearer {config.token.get_secret_value()}"}
        domain = entity_id.split(".")[0]

        if domain == "scene":
            service = "scene/turn_on"
        elif domain == "automation":
            service = "automation/trigger"
        else:
            return f"Entity '{entity_id}' is not a scene or automation."

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{config.url}/api/services/{service}",
                headers=headers,
                json={"entity_id": entity_id},
            )
            resp.raise_for_status()

        return f"OK: Triggered {entity_id}"
