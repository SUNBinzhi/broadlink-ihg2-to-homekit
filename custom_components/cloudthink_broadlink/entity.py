"""Shared entity properties."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import DOMAIN


class CloudThinkEntity(Entity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, device: dict, suffix: str | None = None) -> None:
        self.coordinator = coordinator
        self.device = device
        self.device_id = device["applianceId"]
        self._attr_unique_id = f"{self.device_id}_{suffix}" if suffix else self.device_id
        self._attr_name = suffix if suffix else None

    @property
    def device_info(self) -> DeviceInfo:
        room = self.device.get("roomName") or getattr(self.coordinator, "room", None)
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_id)},
            name=self.device.get("friendlyName") or f"{room or '全屋'}设备",
            manufacturer="BroadLink / CloudThink",
            model=self.device.get("modelName") or None,
            suggested_area=room,
        )

    @property
    def available(self) -> bool:
        return (
            self.coordinator.last_update_success
            and self.device_id not in self.coordinator.failed_ids
            and self.device_id in (self.coordinator.data or {})
        )

    @property
    def state_data(self) -> dict:
        return (self.coordinator.data or {}).get(self.device_id, {})

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))
