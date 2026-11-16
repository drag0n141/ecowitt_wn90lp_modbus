"""DataUpdateCoordinator for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

import logging
import math
import time
from collections import deque
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    INVALID_VALUE,
    RAIN_HOLD_TIME_MINUTES,
    RAIN_RATE_MIN_SECONDS,
    RAIN_RATE_WINDOW_MINUTES,
    REGISTER_COUNT,
    SENSOR_DESCRIPTIONS,
    START_REGISTER,
    STORAGE_VERSION,
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


class Wn90lpModbusCoordinator(
    DataUpdateCoordinator[dict[str, float | str | bool | None]]
):
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
        # Rain detection state (see _update_rain_state).
        self._last_rain_total: float | None = None
        self._last_rain_increase: float | None = None  # time.monotonic()
        # "Rain today": counter value at the start of the current local day,
        # persisted so a restart of Home Assistant does not reset the day.
        self._store: Store = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}.rain_day"
        )
        self._day: str | None = None
        self._day_baseline: float | None = None
        # "Rain rate": (time.monotonic(), counter) samples of the last window.
        self._rate_samples: deque[tuple[float, float]] = deque()

    async def async_load_state(self) -> None:
        """Load the persisted "rain today" baseline (call before first refresh)."""
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            day = stored.get("day")
            baseline = stored.get("baseline")
            if isinstance(day, str) and isinstance(baseline, (int, float)):
                self._day = day
                self._day_baseline = float(baseline)

    def _data_to_save(self) -> dict[str, Any]:
        return {"day": self._day, "baseline": self._day_baseline}

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

    async def _async_update_data(self) -> dict[str, float | str | bool | None]:
        client = await self._async_get_client()

        try:
            result = await client.read_holding_registers(
                address=START_REGISTER,
                count=REGISTER_COUNT,
                device_id=self._unit_id,
            )
        except Exception as err:  # noqa: BLE001 - surface any transport error
            raise UpdateFailed(f"Modbus read failed: {err}") from err

        if result is None or result.isError():
            raise UpdateFailed(f"Modbus error response: {result}")

        raw_registers = result.registers
        data: dict[str, float | str | bool | None] = {}

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
        self._update_rain_state(data)
        self._update_rain_totals(data)

        return data

    def _update_rain_totals(self, data: dict[str, float | str | bool | None]) -> None:
        """Derive "rain today" (mm) and "rain rate" (mm/h) from the fine counter.

        Both use the 0.01 mm counter so they agree with each other. The
        counter is cumulative since the station was powered on:

        - rain today = counter now - counter at the start of the local day
          (baseline, persisted). A counter that goes down (station restart)
          resets the baseline to 0, so everything counted since is today's.
        - rain rate = counter increase over the last RAIN_RATE_WINDOW_MINUTES,
          scaled to mm/h; 0 until there are enough samples.
        """
        total = data.get("rain_counter")
        if not isinstance(total, (int, float)):
            data["rain_today"] = None
            data["rain_rate"] = None
            return

        today = dt_util.now().date().isoformat()
        changed = False
        if self._day != today or self._day_baseline is None:
            self._day = today
            self._day_baseline = float(total)
            changed = True
        elif total < self._day_baseline:
            self._day_baseline = 0.0
            changed = True
        if changed:
            self._store.async_delay_save(self._data_to_save, 10)
        data["rain_today"] = round(total - self._day_baseline, 2)

        now = time.monotonic()
        samples = self._rate_samples
        if samples and total < samples[-1][1]:
            samples.clear()  # counter reset
        samples.append((now, float(total)))
        cutoff = now - RAIN_RATE_WINDOW_MINUTES * 60
        while len(samples) > 1 and samples[1][0] <= cutoff:
            samples.popleft()
        oldest_time, oldest_total = samples[0]
        elapsed = now - oldest_time
        if elapsed < RAIN_RATE_MIN_SECONDS:
            data["rain_rate"] = 0.0
        else:
            data["rain_rate"] = round((total - oldest_total) / (elapsed / 3600), 2)

    def _update_rain_state(self, data: dict[str, float | str | bool | None]) -> None:
        """Derive the on/off "raining" state from the fine rain counter (0.01 mm).

        The WN90LP only reports a cumulative rain counter. It is treated as
        "raining" when the counter increased since the previous poll, and
        stays on for RAIN_HOLD_TIME_MINUTES after the last increase (light
        rain only adds a tick every few minutes). A counter that goes down
        (device reset) just moves the baseline and does not count as rain.
        The state starts "off" after a restart of Home Assistant until the
        next increase is seen.
        """
        total = data.get("rain_counter")
        if not isinstance(total, (int, float)):
            # Invalid reading: unknown. Keep the baseline so a gap does not
            # turn into a bogus increase afterwards.
            data["raining"] = None
            return

        now = time.monotonic()
        if self._last_rain_total is not None and total > self._last_rain_total:
            self._last_rain_increase = now
        self._last_rain_total = total

        data["raining"] = (
            self._last_rain_increase is not None
            and now - self._last_rain_increase <= RAIN_HOLD_TIME_MINUTES * 60
        )

    @staticmethod
    def _add_calculated_sensors(data: dict[str, float | str | bool | None]) -> None:
        """Derive dew point / wind chill from read values."""
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
