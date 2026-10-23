"""Living room environment readings."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass

from .const import DOMAIN
from .entity import CloudThinkEntity

SENSORS = {
    "temperature": ("温度", SensorDeviceClass.TEMPERATURE, "°C"),
    "humidity": ("湿度", SensorDeviceClass.HUMIDITY, "%"),
    "pm25": ("PM2.5", SensorDeviceClass.PM25, "µg/m³"),
    "envCO2": ("二氧化碳", SensorDeviceClass.CO2, "ppm"),
    "envlux": ("照度", SensorDeviceClass.ILLUMINANCE, "lx"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CloudThinkSensor(coordinator, item, key)
        for item in coordinator.devices
        if "ENVIRONMENT_SENSOR" in (item.get("applianceTypes") or [])
        for key in SENSORS
    )


class CloudThinkSensor(CloudThinkEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device, key):
        super().__init__(coordinator, device, key)
        self.key = key
        self._attr_name, self._attr_device_class, self._attr_native_unit_of_measurement = SENSORS[key]

    @property
    def native_value(self):
        return self.state_data.get(self.key)

