"""Dehumidifier exposed through the CloudThink bridge.

云端只提供开关控制；目标湿度可读但设置指令不生效，因此不暴露调节功能。
"""

from __future__ import annotations

from homeassistant.components.humidifier import HumidifierDeviceClass, HumidifierEntity

from .const import DOMAIN
from .entity import CloudThinkEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkDehumidifier(coordinator, item)
        for item in coordinator.devices
        if "DEHUMIDIFIER" in (item.get("applianceTypes") or [])
    )


class CloudThinkDehumidifier(CloudThinkEntity, HumidifierEntity):
    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_min_humidity = 10
    _attr_max_humidity = 98

    @property
    def is_on(self):
        return self.state_data.get("turnOnState") == "ON"

    @property
    def current_humidity(self):
        value = self.state_data.get("humidity")
        return float(value) if value is not None else None

    @property
    def target_humidity(self):
        value = self.state_data.get("targetHumidity")
        return float(value) if value is not None else None

    async def async_turn_on(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOnRequest")

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOffRequest")
