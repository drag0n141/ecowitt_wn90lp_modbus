"""The Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_UNIT_ID, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import Wn90lpModbusCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ecowitt WN90LP Modbus from a config entry."""
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    coordinator = Wn90lpModbusCoordinator(
        hass,
        entry,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        unit_id=entry.data[CONF_UNIT_ID],
        scan_interval=scan_interval,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload the entry whenever options (currently: scan interval) change,
    # so a new coordinator with the updated update_interval is created.
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: Wn90lpModbusCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown_client()
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
