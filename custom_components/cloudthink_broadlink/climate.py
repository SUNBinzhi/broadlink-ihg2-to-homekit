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
    _attr_fan_modes = ["1", "2", "3", "4"]
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
        return str(value) if value is not None else None

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
        speed = int(fan_mode)
        if speed not in (1, 2, 3, 4):
            raise ValueError("Fan speed must be 1–4")
        await self.coordinator.command(self.device, "SetFanSpeedRequest", {"fanSpeed": {"value": speed}})

