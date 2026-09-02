# Ecowitt WN90LP (Modbus) – Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Custom Home Assistant integration for the **Ecowitt WN90LP**, the wired
RS485/Modbus-RTU variant of the Ecowitt WS90 weather sensor. Polls the
device via **Modbus TCP** through an RS485-to-TCP gateway (Waveshare,
Elfin EW11, USR, etc.) — no cloud, no console, fully local.

## Requirements

- A configured **Modbus RTU-to-TCP gateway** wired to the WN90LP's RS485
  port (9600 baud, 8N1, no parity — the WN90LP's own defaults)
- The gateway's IP address and port (usually 502)
- The WN90LP's Modbus unit/slave ID (factory default: `144` / `0x90`)
- Home Assistant 2024.1 or later
- HACS (optional, for easy installation)

## Installation

### Via HACS

1. Add this repository to HACS **Integrations → Custom repositories**
   [![Add repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=drag0n141&repository=ecowitt_wn90lp_modbus&category=integration)
2. Install the "Ecowitt WN90LP (Modbus)" integration
3. Restart Home Assistant
4. Add the integration via **Settings → Devices & Services**
   [![Open your Home Assistant instance and show the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ecowitt_wn90lp)

### Manual

Copy `custom_components/ecowitt_wn90lp` into your Home Assistant
`custom_components` folder and restart.

## Setup

Settings → Devices & Services → Add Integration → **Ecowitt WN90LP
(Modbus)**, then enter:

- **Host**: IP address of your Modbus TCP gateway
- **Port**: usually `502`
- **Unit/Slave ID**: `144` unless you changed it on the device
- **Scan interval**: default `30` seconds

## Sensors

All registers are read in a single Modbus request (function `0x03`,
starting at register `0x0165`, 10 registers), per the official
[Ecowitt WN90LP Modbus RTU specification (V1.0.5, PDF)](https://oss.ecowitt.net/uploads/20241004/WN90LP%20ModbusRTU_V1.0.5_En.pdf).

| Sensor            | Register | Raw → Value                       | Unit  | Enabled by default |
| ------------------ | -------- | ----------------------------------- | ----- | ------------------- |
| Light               | `0x0165` | `raw * 10`                          | lx    | Yes |
| UV Index            | `0x0166` | `raw * 0.1`                         | —     | Yes |
| Temperature         | `0x0167` | `raw * 0.1 - 40`                    | °C    | Yes |
| Humidity            | `0x0168` | `raw`                                | %     | Yes |
| Wind Speed          | `0x0169` | `raw * 0.1`                         | m/s   | Yes |
| Gust Speed          | `0x016A` | `raw * 0.1`                         | m/s   | Yes |
| Wind Direction      | `0x016B` | `raw`                                | °     | Yes |
| Rainfall            | `0x016C` | `raw * 0.1` (0.1 mm resolution counter) | mm    | Yes |
| Absolute Pressure   | `0x016D` | `raw * 0.1`                         | hPa   | Yes |
| Rain Counter (fine) | `0x016E` | `raw * 0.01` (0.01 mm resolution counter) | mm    | No |

A raw value of `0xFFFF` means "invalid/no reading" — the integration
reports the corresponding sensor as `unavailable` in that case instead of
a bogus number.

### Notes from the spec

- `0x0165`–`0x0168`, `0x016C` and `0x016E` update roughly every 8.75 s;
  the wind registers (`0x0169`–`0x016B`) update roughly every 2 s. A
  10–30 s scan interval is a reasonable default.
- The spec explicitly recommends `0x016C` (0.1 mm resolution) as the rain
  counter register for most cases. `0x016E` is the finer-grained 0.01 mm
  alternative — both are read in the same block request, but `0x016E` is
  disabled by default in the entity registry to avoid cluttering the
  entity list; enable it manually if you want the extra precision.

## Wiring reference

| Wire  | Signal | Notes        |
| ----- | ------ | ------------ |
| Red   | VCC    | 5–12 V DC    |
| Black | GND    | GND          |
| Green | 485_A  | RS485 A      |
| White | 485_B  | RS485 B      |

Default Modbus parameters: **9600 baud, 8 data bits, no parity, 1 stop
bit**, slave address `0x90`.

## Not implemented (yet)

- The `0x9C92`–`0x9C9A` "start a measurement" command registers
  (higher-frequency single-shot readings)
- Changing baud rate / device address from within Home Assistant (use
  Ecowitt's own PC tool for that)

## Credits

Register map and scaling reverse-engineered from the official
[Ecowitt "WN90LP ModbusRTU" specification (V1.0.5, PDF)](https://oss.ecowitt.net/uploads/20241004/WN90LP%20ModbusRTU_V1.0.5_En.pdf).
Not affiliated with Ecowitt or Fine Offset.

## License

MIT
