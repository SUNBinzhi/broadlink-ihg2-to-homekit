"""Living room lights.

The exposed device is the mini-app's virtual group "会客组", which supports
on/off, brightness (0-100 %) and color temperature (exposed by the cloud as a
0-100 percentage, not kelvin).
"""

from __future__ import annotations

import asyncio

from homeassistant.components.light import ColorMode, LightEntity

from .const import DOMAIN
from .entity import CloudThinkEntity

MIN_KELVIN = 2700
MAX_KELVIN = 6500


def _pct_to_kelvin(pct: float) -> int:
    pct = max(0.0, min(100.0, pct))
    return int(round(MIN_KELVIN + pct / 100.0 * (MAX_KELVIN - MIN_KELVIN)))


def _kelvin_to_pct(kelvin: float) -> int:
    kelvin = max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
    return int(round((kelvin - MIN_KELVIN) / (MAX_KELVIN - MIN_KELVIN) * 100))


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkLight(coordinator, item)
        for item in coordinator.devices
        if "LIGHT" in (item.get("applianceTypes") or [])
    )


class CloudThinkLight(CloudThinkEntity, LightEntity):
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    @property
    def is_on(self):
        return self.state_data.get("turnOnState") == "ON"

    @property
    def color_mode(self):
        return ColorMode.COLOR_TEMP

    @property
    def brightness(self):
        value = self.state_data.get("brightness")
        # The virtual group reports 0 right after power-on, which is not a real
        # brightness level; treat it as unknown instead of "off at 0 %".
        if not value:
            return None
        return max(0, min(255, int(round(float(value) * 255 / 100))))

    @property
    def color_temp_kelvin(self):
        value = self.state_data.get("colorTemperatureInKelvin")
        if value is None:
            return None
        return _pct_to_kelvin(float(value))

    async def async_turn_on(self, **kwargs):
        if not self.is_on:
            await self.coordinator.command(self.device, "TurnOnRequest")
            # The group ignores a brightness value sent in the same instant as
            # the power-on command; 1 s is enough for the lamps to come up.
            await asyncio.sleep(1.0)

        brightness = kwargs.get("brightness")
        if brightness is not None:
            pct = max(0, min(100, int(round(brightness * 100 / 255))))
            await self.coordinator.command(
                self.device,
                "SetBrightnessPercentageRequest",
                {"brightness": {"value": pct}},
            )

        kelvin = kwargs.get("color_temp_kelvin")
        if kelvin is not None:
            await self.coordinator.command(
                self.device,
                "SetColorTemperatureRequest",
                {"colorTemperatureInKelvin": _kelvin_to_pct(kelvin)},
            )

    async def async_turn_off(self, **kwargs):
        await self.coordinator.command(self.device, "TurnOffRequest")
