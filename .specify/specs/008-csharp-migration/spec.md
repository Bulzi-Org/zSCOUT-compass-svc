# Specification: Migrate zSCOUT-compass-svc from Python FastAPI to C# .NET 10 Minimal API

**Issue**: #8
**Status**: Draft
**Created**: 2026-05-21

## Overview

Rewrite the zSCOUT Compass Hardware Service from Python 3.12 / FastAPI to C# / .NET 10 Minimal API, aligning with the platform-wide C#/.NET 10 standard across all zSCOUT services.

## Requirements

### REQ-001: Identical REST+SSE API Contract

The C# service must expose the same four endpoints with identical JSON response schemas:

- `GET /api/status` → `{ status, deviceAddress, i2cBus, deviceFound, overflow, timestamp }`
- `GET /api/heading` → `{ headingDegrees, x, y, z, temperature, overflow, timestamp }`
- `GET /api/axes` → `{ x, y, z, statusRegister, timestamp }`
- `GET /api/stream/headings` → SSE stream, event name `heading`, payload matches `/api/heading` (minus `overflow`)

camelCase JSON property names must be preserved. The SSE stream accepts `?intervalMs=<int>` query parameter (default 100, min 10, max 10000).

### REQ-002: QMC5883L I2C Driver via System.Device.Gpio

Use `System.Device.Gpio` / `System.Device.I2c` NuGet package for I2C access:

- Bus: configurable via `I2C_BUS` env var (default `1`)
- Address: configurable via `I2C_ADDRESS` env var (default `0x0d`)
- Init sequence: write `0x80` to `REG_CTRL2` (reset), `0x01` to `REG_SET_RESET`, `0x1D` to `REG_CTRL1`
- Read 9 bytes from register `0x00`: X (bytes 0-1), Y (2-3), Z (4-5), Status (6), Temp (7-8), all 16-bit signed little-endian

### REQ-003: Heading Calculation

- `heading = atan2(y, x)` converted to degrees and normalized to 0–360°
- Temperature conversion: `raw / 100.0` (relative Celsius)

### REQ-004: Status Determination

- `"healthy"` — device found, data valid
- `"degraded"` — device found but all-zero axes or overflow flag set
- `"unavailable"` — device not found or communication error

### REQ-005: Graceful Degradation

Service must start and remain responsive even when no I2C device is present. Never crash on I2C failure.

### REQ-006: Configuration via Environment Variables

- `I2C_BUS` (default: `1`)
- `I2C_ADDRESS` (default: `0x0d`, hex string)
- `HTTP_PORT` (default: `5100`)
- `STREAM_INTERVAL_MS` (default: `100`)

### REQ-007: Docker Build

Multi-stage Dockerfile using `debian:bookworm-slim`:
- Build stage: .NET 10 SDK, `dotnet publish`
- Runtime stage: .NET 10 runtime only
- Target platform: `linux/arm64`

### REQ-008: Unit Tests

Unit tests using xUnit with mocked I2C layer:
- Heading calculation edge cases (0°, 90°, 180°, 270°)
- Temperature conversion
- Status determination logic
- REST endpoint responses
- SSE streaming

### REQ-009: Project Structure

```
src/
  ZScout.CompassSvc/
    ZScout.CompassSvc.csproj
    Program.cs
    Qmc5883lDriver.cs
    CompassService.cs
    HeadingCache.cs
    HeadingReaderService.cs
tests/
  ZScout.CompassSvc.Tests/
    ZScout.CompassSvc.Tests.csproj
deploy/
  Dockerfile
  docker-compose.yml
zSCOUT-compass-svc.slnx
```

### REQ-010: CI/CD Updates

Update GitHub Actions workflows to use .NET build/test instead of Python.

## Out of Scope

- Calibration or magnetic declination adjustments
- gRPC or WebSocket endpoints (REST+SSE only)
- Migration of Python code to a separate package — Python files are replaced entirely
