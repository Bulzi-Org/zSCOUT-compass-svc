# Specification: Compass Hardware Service with gRPC API

**Issue**: #1 — Build Compass hardware service container with gRPC API on port 5100
**Status**: Draft
**Author**: SpecKit Agent

## Summary

Build a Tier 2 hardware service container that owns the QMC5883L magnetometer via I2C (`/dev/i2c-1`, address `0x0d`) and exposes compass heading data through a gRPC API on port 5100. This service is the sole owner of I2C compass hardware access in the zSCOUT three-tier architecture. All application containers (scanner, hw-test, config-agent) consume heading data through this service's gRPC API rather than accessing I2C directly.

## Architecture Context

The zSCOUT system follows a three-tier architecture:

- **Tier 1 (Host OS)**: Raspberry Pi CM5 running Debian, exposes `/dev/i2c-1` with `dtparam=i2c_arm=on`
- **Tier 2 (Hardware Services)**: Containerized services that own specific hardware peripherals. The compass service is one such service.
- **Tier 3 (Application Containers)**: Consumers of hardware data via gRPC APIs

```
Host OS (Tier 1) → /dev/i2c-1 (I2C bus)
    │
    ▼ --device /dev/i2c-1
zSCOUT-compass-svc (Tier 2) → gRPC :5100
    │
    ├── zscout-scanner (needs heading for direction-of-arrival)
    ├── zscout-hw-test (validates compass hardware)
    └── zscout-config-agent (status/config)
```

## Functional Requirements

### FR-1: GetHeading RPC

Single snapshot read of the current compass heading. Returns heading in degrees (0–360), raw XYZ axis values, temperature, overflow status, and UTC timestamp.

### FR-2: StreamHeadings RPC

Server-streaming RPC providing continuous heading updates at a configurable interval (default 100ms / 10 Hz). Includes all fields from GetHeading plus data-ready, data-overrun flags, and sample counter.

### FR-3: GetRawAxes RPC

Returns raw X, Y, Z axis values and the status register for calibration purposes.

### FR-4: GetStatus RPC

Health check endpoint returning device availability, I2C bus/address info, data readiness, and health status string ("healthy", "degraded", "unavailable").

## Non-Functional Requirements

### NFR-1: Graceful Degradation

When the QMC5883L sensor is missing, disconnected, or returning errors, the service must not crash. It should return appropriate status ("unavailable" or "degraded") and continue running.

### NFR-2: All-Zero Detection

If all axis values read as zero, the service must detect this condition and report status as "degraded".

### NFR-3: Overflow Monitoring

The OVL flag in the STATUS register must be monitored and reported in heading responses.

### NFR-4: ARM64 Deployment

Docker images must build and run on ARM64 (Raspberry Pi CM5). Container must only require `--device /dev/i2c-1`, not `--privileged`.

### NFR-5: Configurability

I2C bus number, device address, and gRPC port must be configurable via environment variables.

## Acceptance Criteria

- [ ] Dockerfile builds for ARM64
- [ ] Container reads QMC5883L at 0x0d via /dev/i2c-1 and computes heading
- [ ] gRPC `GetHeading` returns current heading, raw XYZ, temperature
- [ ] gRPC `StreamHeadings` provides continuous updates at configurable rate
- [ ] gRPC `GetStatus` returns device availability and health
- [ ] Handles missing/disconnected sensor gracefully (returns unavailable, does not crash)
- [ ] All-zero axis data detected and reported as degraded
- [ ] Overflow flag monitored and reported
- [ ] Container requires only `--device /dev/i2c-1`, not `--privileged`
- [ ] GHCR publish workflow for ARM64 builds

## Success Criteria

- All four gRPC RPCs function correctly with real QMC5883L hardware
- Service starts and remains stable with no sensor connected (graceful degradation)
- Heading calculation matches expected values within ±1° for known axis inputs
- Streaming endpoint maintains target update rate without drift
- Docker image size under 200MB
- Unit tests pass with mocked I2C layer
