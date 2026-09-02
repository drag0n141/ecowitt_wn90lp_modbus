"""DataUpdateCoordinator for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

import logging
import math
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


def _calculate_dew_point(temperature_c: float, humidity_pct: float) -> float:
    """Dew point via the Magnus-Tetens approximation.

    Standard meteorological formula; accurate to within about 0.1-0.2 C
    for the temperature/humidity ranges this sensor operates in.
    """
    a, b = 17.27, 237.7
    alpha = ((a * temperature_c) / (b + temperature_c)) + math.log(
        humidity_pct / 100.0
    )
    return (b * alpha) / (a - alpha)


def _calculate_wind_chill(temperature_c: float, wind_speed_ms: float) -> float:
    """Wind chill via the North American/JAG-TI 2001 formula.

    Only meteorologically valid for temperature <= 10 C and wind speed
    >= 4.8 km/h. Outside that range, most weather services just show the
    actual air temperature as the "feels like" value instead of applying
    the formula (which produces nonsensical results out of range) - this
    does the same.
    """
    wind_kmh = wind_speed_ms * 3.6

    if temperature_c > 10 or wind_kmh < 4.8:
        return temperature_c

    return (
        13.12
        + 0.6215 * temperature_c
        - 11.37 * wind_kmh**0.16
        + 0.3965 * temperature_c * wind_kmh**0.16
    )


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
            if description.register_index is None:
                # Calculated sensor - filled in below once every raw
                # register has been read and scaled.
                continue

            raw = raw_registers[description.register_index]

            if raw == INVALID_VALUE:
                data[description.key] = None
                continue

            if description.signed and raw > 0x7FFF:
                raw -= 0x10000

            value = raw * description.scale + description.offset
            data[description.key] = round(value, 2)

        self._add_calculated_sensors(data)

        return data

    @staticmethod
    def _add_calculated_sensors(data: dict[str, float | None]) -> None:
        """Derive dew point / wind chill from the already-read values."""
        temperature = data.get("temperature")
        humidity = data.get("humidity")
        wind_speed = data.get("wind_speed")

        data["dew_point"] = (
            round(_calculate_dew_point(temperature, humidity), 1)
            if temperature is not None and humidity is not None and humidity > 0
            else None
        )

        data["wind_chill"] = (
            round(_calculate_wind_chill(temperature, wind_speed), 1)
            if temperature is not None and wind_speed is not None
            else None
        )

    async def async_shutdown_client(self) -> None:
        """Close the Modbus client connection on unload."""
        if self._client is not None:
            self._client.close()
            self._client = None
