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
    """Set up the WN90LP connectivity diagnostic entity."""
    coordinator: Wn90lpModbusCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME, MODEL),
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=None,
    )

    async_add_entities(
        [Wn90lpConnectivityBinarySensor(coordinator, entry, device_info)]
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
    """

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Connectivity"

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
