"""CloudThink BroadLink multi-room integration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CloudThinkAPI
from .const import DATA_DIR, DEFAULT_ROOM, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

BACKGROUND_LIGHTS = {"defaultbglight", "面板背景灯", "厨房复合开关背景灯"}
CONTROL_TYPES = {"AIR_CONDITION", "CURTAIN", "CURT_SIMP", "AIR_FRESHER", "ENVIRONMENT_SENSOR"}


def pick_lights(
    devices: list[dict],
    room: str,
    preferred: str | None = None,
    extras: list[str] | None = None,
) -> list[dict]:
    """Pick light entities for a room.

    Preference order: explicit choice, the room's virtual group, any virtual
    group, then every non-background light in the room (rooms without a group).
    Extra lights named in the entry options are appended on top of the group,
    so a room keeps its group switch and gains the lamps the group misses.
    """
    candidates = [
        d
        for d in devices
        if d.get("roomName") == room
        and "LIGHT" in (d.get("applianceTypes") or [])
        and d.get("friendlyName") not in BACKGROUND_LIGHTS
    ]
    picked: list[dict] = []
    if preferred and preferred not in ("", "自动"):
        picked = [d for d in candidates if d.get("friendlyName") == preferred][:1]
    if not picked:
        picked = [d for d in candidates if d.get("friendlyName") == f"{room}的灯"][:1]
    if not picked and room == "客厅":
        picked = [d for d in candidates if d.get("friendlyName") == "会客组"][:1]
    if not picked:
        picked = [d for d in candidates if (d.get("friendlyName") or "").endswith("组")][:1]
    if not picked:
        picked = list(candidates)
    if extras:
        seen = {d.get("applianceId") for d in picked}
        for name in extras:
            for d in candidates:
                if d.get("friendlyName") == name and d.get("applianceId") not in seen:
                    picked.append(d)
                    seen.add(d.get("applianceId"))
    return picked


def selected_devices(
    all_devices: list[dict],
    room: str,
    light_name: str | None = None,
    extra_lights: list[str] | None = None,
) -> list[dict]:
    """Expose one room: climate, covers, fresh air, sensors and one light group."""
    selected: list[dict] = []
    for device in all_devices:
        if device.get("roomName") != room:
            continue
        name = device.get("friendlyName") or ""
        types = set(device.get("applianceTypes") or [])
        if types & {"CURTAIN", "CURT_SIMP"} and name.startswith(f"{room}的"):
            # Virtual aliases such as "主卧的窗帘" duplicate the real motors.
            continue
        if CONTROL_TYPES.intersection(types):
            selected.append(device)
    lights = pick_lights(all_devices, room, light_name, extra_lights)
    for light in lights:
        rename = f"{room}的灯" if len(lights) == 1 else (light.get("friendlyName") or "")
        selected.append({**light, "friendlyName": rename} if rename else light)
    return selected


class CloudThinkCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    def __init__(self, hass: HomeAssistant, api: CloudThinkAPI, devices: list[dict], room: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"CloudThink {room}",
            update_interval=timedelta(seconds=20),
        )
        self.api = api
        self.devices = devices
        self.room = room
        self.devices_by_id = {item["applianceId"]: item for item in devices}
        self.command_lock = asyncio.Lock()
        self.failed_ids: set[str] = set()

    async def _async_update_data(self) -> dict[str, dict]:
        # Limit concurrent cloud calls to avoid flooding the house proxy.
        semaphore = asyncio.Semaphore(4)
        previous = dict(self.data or {})

        async def read(device: dict) -> tuple[str, dict | None]:
            async with semaphore:
                try:
                    state = await self.hass.async_add_executor_job(self.api.state, device)
                    return device["applianceId"], state
                except Exception as exc:
                    _LOGGER.warning(
                        "State read failed for %s: %s", device.get("friendlyName"), type(exc).__name__
                    )
                    return device["applianceId"], None

        results = await asyncio.gather(*(read(device) for device in self.devices))
        successful = 0
        failed: set[str] = set()
        for device_id, state in results:
            if state is not None:
                previous[device_id] = state
                successful += 1
            else:
                failed.add(device_id)
        self.failed_ids = failed
        if successful == 0:
            raise UpdateFailed(f"All {self.room} state requests failed")
        return previous

    async def command(self, device: dict, name: str, extra: dict | None = None) -> None:
        async with self.command_lock:
            await self.hass.async_add_executor_job(self.api.call, name, device, extra)
            state = await self.hass.async_add_executor_job(self.api.state, device)
            updated = dict(self.data or {})
            updated[device["applianceId"]] = state
            self.failed_ids.discard(device["applianceId"])
            self.async_set_updated_data(updated)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    room = entry.data.get("room", DEFAULT_ROOM)
    light_name = entry.options.get("light", entry.data.get("light"))
    extra_lights = entry.options.get("extra_lights") or entry.data.get("extra_lights") or []
    data_path = Path(hass.config.path(DATA_DIR))
    session_path = data_path / "session.json"
    devices_path = data_path / "devices.json"
    try:
        all_devices = await hass.async_add_executor_job(
            lambda: json.loads(devices_path.read_text(encoding="utf-8"))
        )
        devices = selected_devices(all_devices, room, light_name, extra_lights)
        if not devices or not session_path.is_file():
            raise ValueError("Missing devices or session")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _LOGGER.error("CloudThink configuration files are invalid: %s", type(exc).__name__)
        return False
    coordinator = CloudThinkCoordinator(hass, CloudThinkAPI(session_path), devices, room)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok
