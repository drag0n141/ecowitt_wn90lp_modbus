# Changelog

All notable changes to this project are documented here. Versioning
follows [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH,
where MINOR adds backward-compatible functionality and PATCH is a
fix with no new functionality.

## [0.9.0] - 2026-11-16

### Added

- "Rain Today" sensor (German: "Niederschlag heute"): rain since local
  midnight, derived from the fine rain counter; the day's baseline is
  persisted across restarts
- "Rain Rate" sensor (German: "Regenrate"): rain intensity in mm/h over
  a 10 minute window

## [0.8.1] - 2026-11-15

### Fixed

- The rain sensors showed small amounts as "0 mm" because Home Assistant
  had picked 0 decimals as the display precision. "Rainfall" now shows
  1 decimal and "Rain Counter (0.01 mm)" 2 decimals

## [0.8.0] - 2026-11-15

### Added

- "Raining" binary sensor (German: "Regen"): on when the rain counter
  increased recently, off after 10 minutes without an increase.
  Unavailable while the rain reading is invalid

## [0.7.1] - 2026-11-15

### Changed

- German name of the wind chill sensor is now "Gefühlte Temperatur
  (Wind)" instead of the English loanword (#16)

## [0.7.0] - 2026-11-15

### Added

- "Wind Direction (Compass)" sensor: 16-point compass heading derived
  from the wind direction, with translated states (German: NNO, O,
  OSO, ...) (#15)
- Translated entity names (English and German) for all sensors and the
  connectivity diagnostic entity (#15)

## [0.6.1] - 2026-11-14

### Fixed

- Modbus reads failed with newer pymodbus (`unexpected keyword
  argument 'slave'`); now uses `device_id` and requires
  `pymodbus>=3.10.0` (#14)

## [0.6.0] - 2026-09-02

### Added

- Calculated Dew Point and Wind Chill sensors, derived client-side
  from temperature/humidity/wind speed - no extra Modbus reads (#12)

## [0.5.0] - 2026-09-02

### Added

- Fine-resolution rain counter sensor (register `0x016E`, 0.01 mm),
  disabled by default since the spec recommends the existing
  `0x016C`-based "Rainfall" sensor for most cases (#9)

## [0.4.0] - 2026-09-02

### Added

- "Connectivity" diagnostic binary sensor reflecting whether the last
  Modbus poll succeeded, always visible regardless of coordinator
  state (#8)

## [0.3.0] - 2026-09-02

### Added

- Reconfigure flow: host, port, unit/slave ID and scan interval can
  now be changed in place via Settings → Devices & Services →
  Reconfigure, without deleting and recreating the config entry (#7)

### Changed

- Raised minimum supported Home Assistant version to 2024.12.0
  (required by the reconfigure flow APIs)

## [0.2.3] - 2026-09-02

### Fixed

- Unit/slave ID and scan interval fields no longer render as sliders
  in the config/options flow forms; both now use an explicit
  `NumberSelector` in box mode for precise numeric entry (#6)

## [0.2.2] - 2026-09-02

### Fixed

- Broken specification link in the README (was pointing at the
  generic ecowitt.com homepage instead of the actual WN90LP ModbusRTU
  PDF) (#5)

## [0.2.1] - 2026-09-02

### Added

- "My Home Assistant" badges in the README for one-click HACS
  repository install and config flow start (#4)

## [0.2.0] - 2026-09-02

### Added

- Options flow to adjust the Modbus scan interval after setup,
  without recreating the config entry (#2)

## [0.1.0] - 2026-09-02

### Added

- Initial release: HACS-installable Modbus TCP integration for the
  Ecowitt WN90LP
- Config flow (host, port, unit/slave ID, scan interval) with
  connection validation
- `DataUpdateCoordinator` polling all 9 core registers (`0x0165`-
  `0x016D`) in a single Modbus read via `pymodbus`
- Sensors: Light, UV Index, Temperature, Humidity, Wind Speed, Gust
  Speed, Wind Direction, Rainfall, Absolute Pressure
- Invalid readings (`0xFFFF`) reported as `unavailable` instead of a
  bogus value

[0.9.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/releases/tag/v0.6.0
[0.5.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/releases/tag/v0.1.0
