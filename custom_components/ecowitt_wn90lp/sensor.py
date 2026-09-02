"""Sensor platform for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_UNIT_ID, DOMAIN, MANUFACTURER, MODEL, SENSOR_DESCRIPTIONS
from .coordinator import Wn90lpModbusCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WN90LP sensors from a config entry."""
    coordinator: Wn90lpModbusCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME, MODEL),
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=None,
    )

    entities = [
        Wn90lpSensor(coordinator, entry, description, device_info)
        for description in SENSOR_DESCRIPTIONS
    ]
    async_add_entities(entities)


class Wn90lpSensor(CoordinatorEntity[Wn90lpModbusCoordinator], SensorEntity):
    """Representation of a single WN90LP Modbus register as a sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: Wn90lpModbusCoordinator,
        entry: ConfigEntry,
        description,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._attr_entity_registry_enabled_default = description.enabled_by_default
        if description.icon:
            self._attr_icon = description.icon
        self._attr_device_info = device_info

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._description.key)

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get(self._description.key) is not None
        )
