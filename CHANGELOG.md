# Changelog

All notable changes to this project are documented here. Versioning
follows [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH,
where MINOR adds backward-compatible functionality and PATCH is a
fix with no new functionality.

## [Unreleased]

- Calculated Dew Point and Wind Chill sensors (#10)

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

[Unreleased]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/drag0n141/ecowitt_wn90lp_modbus/releases/tag/v0.1.0
