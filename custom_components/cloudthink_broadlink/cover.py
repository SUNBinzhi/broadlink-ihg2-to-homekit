"""Living room curtains and sheer curtains."""

from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverEntityFeature

from .const import DOMAIN
from .entity import CloudThinkEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkCover(coordinator, item)
        for item in coordinator.devices
        if {"CURTAIN", "CURT_SIMP"}.intersection(item.get("applianceTypes") or [])
    )


class CloudThinkCover(CloudThinkEntity, CoverEntity):
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.SET_POSITION

    @property
    def current_cover_position(self):
        value = self.state_data.get("degree")
        return int(value) if value is not None else None

    @property
    def is_closed(self):
        position = self.current_cover_position
        return position == 0 if position is not None else None

    async def async_open_cover(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOnRequest")

    async def async_close_cover(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOffRequest")

    async def async_set_cover_position(self, **kwargs):
        position = max(0, min(100, int(kwargs["position"])))
        await self.coordinator.command(self.device, "TurnOnRequest", {"DeltaValue": {"value": position}})

