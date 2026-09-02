"""Config flow for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_UNIT_ID,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# NOTE: a plain `vol.All(vol.Coerce(int), vol.Range(min=..., max=...))` gets
# rendered by the HA frontend as a *slider* for small ranges, which is
# unusable for something like a Modbus unit/slave ID (you want to type the
# exact number, not drag a handle). Using an explicit NumberSelector with
# mode=BOX forces a plain numeric text field instead.
_UNIT_ID_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, max=255, step=1, mode=selector.NumberSelectorMode.BOX
        )
    ),
    vol.Coerce(int),
)

_SCAN_INTERVAL_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=5,
            max=3600,
            step=1,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement="s",
        )
    ),
    vol.Coerce(int),
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): _UNIT_ID_SELECTOR,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): _SCAN_INTERVAL_SELECTOR,
    }
)


async def _async_validate_connection(host: str, port: int, unit_id: int) -> None:
    """Try a single Modbus read to make sure the gateway/device answers."""
    from pymodbus.client import AsyncModbusTcpClient

    from .const import REGISTER_COUNT, START_REGISTER

    client = AsyncModbusTcpClient(host=host, port=port)
    try:
        await client.connect()
        if not client.connected:
            raise CannotConnect

        result = await client.read_holding_registers(
            address=START_REGISTER, count=REGISTER_COUNT, slave=unit_id
        )
        if result is None or result.isError():
            raise CannotConnect
    finally:
        client.close()


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ecowitt WN90LP Modbus."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:"
                f"{user_input[CONF_UNIT_ID]}"
            )
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_UNIT_ID],
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during WN90LP setup")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Let the user change host/port/unit-id/scan-interval in place.

        Unlike the options flow (scan interval only), this covers every
        field from the initial setup - useful if the gateway's IP changed,
        or the device's unit/slave ID was reassigned on the Modbus bus.
        """
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                await _async_validate_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input[CONF_UNIT_ID],
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during WN90LP reconfigure")
                errors["base"] = "unknown"
            else:
                unique_id = (
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:"
                    f"{user_input[CONF_UNIT_ID]}"
                )
                await self.async_set_unique_id(unique_id)
                # If the recomputed unique_id still belongs to *this* entry,
                # this updates its data and reloads it, then aborts the flow
                # with "reconfigure_successful". If it now collides with a
                # *different* entry, it aborts with "already_configured"
                # instead - both are exactly what we want here.
                self._abort_if_unique_id_configured(updates=user_input)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, reconfigure_entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow for an existing config entry."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for an existing Ecowitt WN90LP Modbus entry.

    Currently exposes a single setting: the Modbus poll interval. The
    WN90LP returns all of its registers in one contiguous block read, so
    unlike integrations that poll many registers at different priorities
    (fast-changing vs. slow-changing), a single interval is sufficient
    here. For changing host/port/unit-id, use "Reconfigure" instead.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=current_scan_interval
                ): _SCAN_INTERVAL_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the Modbus gateway/device."""
