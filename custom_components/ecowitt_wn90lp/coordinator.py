"""DataUpdateCoordinator for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INVALID_VALUE,
    REGISTER_COUNT,
    SENSOR_DESCRIPTIONS,
    START_REGISTER,
)

_LOGGER = logging.getLogger(__name__)


class Wn90lpModbusCoordinator(DataUpdateCoordinator[dict[str, float | None]]):
    """Polls the WN90LP via Modbus TCP and scales the raw registers."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        host: str,
        port: int,
        unit_id: int,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._unit_id = unit_id
        self._entry = entry
        self._client: Any | None = None

    async def _async_get_client(self) -> Any:
        """Lazily create (and reuse) the async Modbus TCP client."""
        if self._client is None:
            # Imported lazily so config-flow validation / HA startup doesn't
            # hard-fail if pymodbus isn't installed yet.
            from pymodbus.client import AsyncModbusTcpClient

            self._client = AsyncModbusTcpClient(host=self._host, port=self._port)

        if not self._client.connected:
            await self._client.connect()
            if not self._client.connected:
                raise UpdateFailed(
                    f"Could not connect to Modbus gateway {self._host}:{self._port}"
                )

        return self._client

    async def _async_update_data(self) -> dict[str, float | None]:
        client = await self._async_get_client()

        try:
            result = await client.read_holding_registers(
                address=START_REGISTER,
                count=REGISTER_COUNT,
                slave=self._unit_id,
            )
        except Exception as err:  # noqa: BLE001 - surface any transport error
            raise UpdateFailed(f"Modbus read failed: {err}") from err

        if result is None or result.isError():
            raise UpdateFailed(f"Modbus error response: {result}")

        raw_registers = result.registers
        data: dict[str, float | None] = {}

        for description in SENSOR_DESCRIPTIONS:
            raw = raw_registers[description.register_index]

            if raw == INVALID_VALUE:
                data[description.key] = None
                continue

            if description.signed and raw > 0x7FFF:
                raw -= 0x10000

            value = raw * description.scale + description.offset
            data[description.key] = round(value, 2)

        return data

    async def async_shutdown_client(self) -> None:
        """Close the Modbus client connection on unload."""
        if self._client is not None:
            self._client.close()
            self._client = None
