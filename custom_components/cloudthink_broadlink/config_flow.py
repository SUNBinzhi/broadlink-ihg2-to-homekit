"""Add one integration entry per room."""

from __future__ import annotations

import json
from pathlib import Path

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

from .const import DATA_DIR, DOMAIN

AUTO = "自动"


async def _load_devices(hass) -> list[dict]:
    path = Path(hass.config.path(DATA_DIR)) / "devices.json"

    def read() -> list[dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    return await hass.async_add_executor_job(read)


class CloudThinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._room: str | None = None

    async def async_step_user(self, user_input: dict | None = None):
        devices = await _load_devices(self.hass)
        rooms = sorted({d.get("roomName") for d in devices if d.get("roomName")})
        if not rooms:
            return self.async_abort(reason="missing_files")

        if user_input is not None:
            self._room = user_input["room"]
            return await self.async_step_light()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("room", default=rooms[0]): vol.In(rooms)}),
        )

    async def async_step_light(self, user_input: dict | None = None):
        devices = await _load_devices(self.hass)
        room = self._room or ""
        names = sorted(
            {
                d.get("friendlyName")
                for d in devices
                if d.get("roomName") == room
                and "LIGHT" in (d.get("applianceTypes") or [])
                and d.get("friendlyName")
            }
        )

        if user_input is not None:
            await self.async_set_unique_id(f"room_{room}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"全屋智控 · {room}",
                data={"room": room, "light": user_input.get("light", AUTO)},
            )

        return self.async_show_form(
            step_id="light",
            data_schema=vol.Schema({vol.Optional("light", default=AUTO): vol.In([AUTO] + names)}),
            description_placeholders={"room": room},
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return CloudThinkOptionsFlow()


class CloudThinkOptionsFlow(config_entries.OptionsFlow):
    """Let a room add extra lights next to its virtual group."""

    async def async_step_init(self, user_input: dict | None = None):
        entry = self.config_entry
        devices = await _load_devices(self.hass)
        room = entry.data.get("room", "")
        names = sorted(
            {
                d.get("friendlyName")
                for d in devices
                if d.get("roomName") == room
                and "LIGHT" in (d.get("applianceTypes") or [])
                and d.get("friendlyName")
            }
        )
        current_light = entry.options.get("light", entry.data.get("light", AUTO))
        current_extras = entry.options.get("extra_lights", entry.data.get("extra_lights") or [])

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    "light": user_input.get("light", AUTO),
                    "extra_lights": user_input.get("extra_lights", []),
                },
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("light", default=current_light): vol.In([AUTO] + names),
                    vol.Optional("extra_lights", default=current_extras): cv.multi_select(
                        {name: name for name in names}
                    ),
                }
            ),
            description_placeholders={"room": room},
        )
