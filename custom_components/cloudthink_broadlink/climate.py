"""Daikin AC exposed through the CloudThink bridge."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN
from .entity import CloudThinkEntity

_TO_CLOUD = {
    HVACMode.COOL: "COOL",
    HVACMode.HEAT: "HEAT",
    HVACMode.FAN_ONLY: "FAN",
    HVACMode.DRY: "DEHUMIDIFICATION",
    HVACMode.AUTO: "AUTO",
}
_FROM_CLOUD = {value: key for key, value in _TO_CLOUD.items()}

# 云端风速档位：1=自动 2=低 3=中 4=高（与微信小程序显示一致）
_FAN_TO_CLOUD = {"自动": 1, "低": 2, "中": 3, "高": 4}
_FAN_FROM_CLOUD = {value: key for key, value in _FAN_TO_CLOUD.items()}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkClimate(coordinator, item)
        for item in coordinator.devices
        if "AIR_CONDITION" in (item.get("applianceTypes") or [])
    )


class CloudThinkClimate(CloudThinkEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.FAN_ONLY, HVACMode.DRY, HVACMode.AUTO]
    _attr_fan_modes = ["自动", "低", "中", "高"]
    _attr_min_temp = 16
    _attr_max_temp = 30
    _attr_target_temperature_step = 1

    @property
    def hvac_mode(self):
        if self.state_data.get("turnOnState") != "ON":
            return HVACMode.OFF
        return _FROM_CLOUD.get(self.state_data.get("mode"), HVACMode.AUTO)

    @property
    def current_temperature(self):
        return self.state_data.get("temperature")

    @property
    def target_temperature(self):
        return self.state_data.get("targetTemperature")

    @property
    def fan_mode(self):
        value = self.state_data.get("fanSpeed")
        if value is None:
            return None
        return _FAN_FROM_CLOUD.get(int(value), str(value))

    async def async_turn_on(self):
        await self.coordinator.command(self.device, "TurnOnRequest")

    async def async_turn_off(self):
        await self.coordinator.command(self.device, "TurnOffRequest")

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.command(self.device, "TurnOffRequest")
            return
        if self.state_data.get("turnOnState") != "ON":
            await self.coordinator.command(self.device, "TurnOnRequest")
        await self.coordinator.command(
            self.device, "SetModeRequest",
            {"mode": {"deviceType": "AIR_CONDITION", "value": _TO_CLOUD[hvac_mode]}},
        )

    async def async_set_temperature(self, **kwargs):
        value = int(kwargs["temperature"])
        if not 16 <= value <= 30:
            raise ValueError("Target temperature must be 16–30°C")
        await self.coordinator.command(
            self.device, "SetTemperatureRequest",
            {"targetTemperature": {"value": value, "scale": "CELSIUS"}},
        )

    async def async_set_fan_mode(self, fan_mode):
        if fan_mode not in _FAN_TO_CLOUD:
            raise ValueError(f"Unknown fan mode: {fan_mode}")
        await self.coordinator.command(
            self.device, "SetFanSpeedRequest", {"fanSpeed": {"value": _FAN_TO_CLOUD[fan_mode]}}
        )

