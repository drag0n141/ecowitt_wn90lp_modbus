"""Constants for the Ecowitt WN90LP Modbus integration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

DOMAIN: Final = "ecowitt_wn90lp"

# --- Config entry keys -------------------------------------------------
CONF_UNIT_ID: Final = "unit_id"

DEFAULT_NAME: Final = "Ecowitt WN90LP"
DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 144  # 0x90 - Ecowitt factory default slave address
DEFAULT_SCAN_INTERVAL: Final = 30  # seconds

MANUFACTURER: Final = "Ecowitt"
MODEL: Final = "WN90LP"

# --- Modbus register layout --------------------------------------------
# Source: Ecowitt "WN90LP ModbusRTU" specification (V1.0.5), section 1.3.
# A single Read Holding Registers request (function 0x03) starting at
# register 0x0165 for 10 registers returns all fields below in one shot -
# the main weather block (0x0165-0x016D) plus the finer-resolution rain
# counter at 0x016E, which sits directly adjacent to it:
#   0x90 0x03 0x01 0x65 0x00 0x0A ...
START_REGISTER: Final = 0x0165
REGISTER_COUNT: Final = 10

# Sentinel value the sensor reports when a measurement is invalid/unavailable.
INVALID_VALUE: Final = 0xFFFF

# UV Index has no HA-native unit; use a plain, descriptive string.
UV_INDEX: Final = "UV index"


@dataclass(frozen=True, kw_only=True)
class Wn90lpSensorDescription:
    """Describes a single Modbus register exposed as a sensor."""

    key: str
    name: str
    register_index: int  # offset from START_REGISTER, 0-based
    scale: float = 1.0
    offset: float = 0.0
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    icon: str | None = None
    signed: bool = False
    enabled_by_default: bool = True


# Register order exactly as returned by the WN90LP for a single block read
# starting at 0x0165 (see spec examples 1 & 2).
SENSOR_DESCRIPTIONS: Final[tuple[Wn90lpSensorDescription, ...]] = (
    Wn90lpSensorDescription(
        key="light",
        name="Light",
        register_index=0,  # 0x0165
        scale=10,
        unit="lx",
        state_class="measurement",
        icon="mdi:brightness-6",
    ),
    Wn90lpSensorDescription(
        key="uv_index",
        name="UV Index",
        register_index=1,  # 0x0166
        scale=0.1,
        unit=UV_INDEX,
        state_class="measurement",
        icon="mdi:weather-sunny-alert",
    ),
    Wn90lpSensorDescription(
        key="temperature",
        name="Temperature",
        register_index=2,  # 0x0167
        scale=0.1,
        # Raw value has a fixed +400 (40.0 C) offset baked in by the device.
        offset=-40.0,
        unit=UnitOfTemperature.CELSIUS,
        device_class="temperature",
        state_class="measurement",
    ),
    Wn90lpSensorDescription(
        key="humidity",
        name="Humidity",
        register_index=3,  # 0x0168
        unit=PERCENTAGE,
        device_class="humidity",
        state_class="measurement",
    ),
    Wn90lpSensorDescription(
        key="wind_speed",
        name="Wind Speed",
        register_index=4,  # 0x0169
        scale=0.1,
        unit=UnitOfSpeed.METERS_PER_SECOND,
        device_class="wind_speed",
        state_class="measurement",
    ),
    Wn90lpSensorDescription(
        key="gust_speed",
        name="Gust Speed",
        register_index=5,  # 0x016A
        scale=0.1,
        unit=UnitOfSpeed.METERS_PER_SECOND,
        device_class="wind_speed",
        state_class="measurement",
        icon="mdi:weather-windy",
    ),
    Wn90lpSensorDescription(
        key="wind_direction",
        name="Wind Direction",
        register_index=6,  # 0x016B
        unit="\u00b0",
        state_class="measurement",
        icon="mdi:compass-outline",
    ),
    Wn90lpSensorDescription(
        key="rainfall",
        name="Rainfall",
        register_index=7,  # 0x016C - 0.1 mm resolution rain counter
        scale=0.1,
        unit=UnitOfLength.MILLIMETERS,
        device_class="precipitation",
        state_class="total_increasing",
        icon="mdi:weather-pouring",
    ),
    Wn90lpSensorDescription(
        key="pressure",
        name="Absolute Pressure",
        register_index=8,  # 0x016D
        scale=0.1,
        unit=UnitOfPressure.HPA,
        device_class="pressure",
        state_class="measurement",
    ),
    Wn90lpSensorDescription(
        key="rain_counter",
        name="Rain Counter (0.01 mm)",
        register_index=9,  # 0x016E - finer-resolution rain counter
        scale=0.01,
        unit=UnitOfLength.MILLIMETERS,
        device_class="precipitation",
        state_class="total_increasing",
        icon="mdi:weather-pouring",
        # The spec itself recommends 0x016C ("rainfall" above) for most
        # cases; this is the finer-grained alternative, off by default so
        # it doesn't clutter the entity list for people who don't need it.
        enabled_by_default=False,
    ),
)
