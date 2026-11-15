"""Binary sensor platform for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import Wn90lpModbusCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WN90LP binary sensors (rain + connectivity diagnostic)."""
    coordinator: Wn90lpModbusCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME, MODEL),
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=None,
    )

    async_add_entities(
        [
            Wn90lpRainBinarySensor(coordinator, entry, device_info),
            Wn90lpConnectivityBinarySensor(coordinator, entry, device_info),
        ]
    )


class Wn90lpRainBinarySensor(
    CoordinatorEntity[Wn90lpModbusCoordinator], BinarySensorEntity
):
    """On while it is raining, derived from the rain counter.

    The coordinator turns the cumulative rain counter into a boolean (on
    when the counter increased recently, see `RAIN_HOLD_TIME_MINUTES`).
    The name comes from the translations (entity.binary_sensor.raining).
    Unavailable while the rain reading is invalid.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "raining"
    _attr_icon = "mdi:weather-rainy"

    def __init__(
        self,
        coordinator: Wn90lpModbusCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_raining"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("raining")

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.get("raining") is not None
        )


class Wn90lpConnectivityBinarySensor(
    CoordinatorEntity[Wn90lpModbusCoordinator], BinarySensorEntity
):
    """Diagnostic entity reflecting whether the last Modbus poll succeeded.

    The weather sensors simply go `unavailable` when a coordinator update
    fails (the default CoordinatorEntity behaviour) - easy to miss unless
    you're looking at that specific sensor. This entity stays visible at
    all times (its `available` is hardcoded to True) and just flips
    on/off, so a silent gateway/device outage shows up as a single
    diagnostic entity turning "off" instead of nine sensors quietly
    going stale.

    It deliberately has no explicit name: with `_attr_has_entity_name` HA
    falls back to the (translated) name of the device class, so it shows
    up as "Connectivity" / "Konnektivität" depending on the language.
    """

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: Wn90lpModbusCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_connectivity"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool:
        """Return True if the last Modbus poll succeeded."""
        return self.coordinator.last_update_success

    @property
    def available(self) -> bool:
        # Deliberately always available: this entity's entire purpose is
        # to report connectivity, so it must never itself go unavailable
        # when the coordinator update fails - that would defeat the point.
        return True
