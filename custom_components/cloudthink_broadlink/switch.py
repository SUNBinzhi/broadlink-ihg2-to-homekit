"""Living room fresh air unit."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from .const import DOMAIN
from .entity import CloudThinkEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkSwitch(coordinator, item)
        for item in coordinator.devices
        if "AIR_FRESHER" in (item.get("applianceTypes") or [])
    )


class CloudThinkSwitch(CloudThinkEntity, SwitchEntity):
    @property
    def is_on(self):
        return self.state_data.get("turnOnState") == "ON"

    async def async_turn_on(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOnRequest")

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOffRequest")

