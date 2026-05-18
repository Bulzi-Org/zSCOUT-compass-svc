# Implementation Plan: Compass Hardware Service

**Issue**: #1
**Spec**: `spec.md`

## Tech Stack

- **Language**: Python 3.12
- **gRPC**: grpcio + grpcio-tools (protobuf code generation)
- **I2C**: smbus2 (pure Python SMBus wrapper)
- **Protobuf**: protobuf runtime
- **Testing**: pytest + pytest-asyncio
- **Container**: debian:bookworm-slim (ARM64)
- **CI/CD**: GitHub Actions → GHCR

## Project Structure

```
src/
  proto/
    compass.proto              # gRPC service definition
  compass_svc/
    __init__.py
    generated/                 # protoc-generated Python code
      compass_pb2.py
      compass_pb2_grpc.py
    i2c_driver.py              # QMC5883L register-level I2C access
    compass.py                 # Heading calculation, temperature, status logic
    server.py                  # gRPC server implementation
    config.py                  # Environment variable configuration
    __main__.py                # Entry point
tests/
  __init__.py
  test_i2c_driver.py           # Mocked I2C register reads
  test_compass.py              # Heading calculation, edge cases
  test_server.py               # gRPC endpoint tests
  conftest.py                  # Shared fixtures
deploy/
  Dockerfile                   # Multi-stage ARM64 build
  docker-compose.yml           # Service definition with device mapping
.github/
  workflows/
    publish.yml                # GHCR publish on push to main / tags
pyproject.toml                 # Project metadata, dependencies, dev deps
```

## Architecture

Three-layer design within the service:

1. **I2C Driver Layer** (`i2c_driver.py`): Direct register access via smbus2. Reads raw bytes from QMC5883L registers. Configures CTRL1 for continuous mode (200Hz ODR, 8G range, 512 OSR). Handles I2C errors and device detection.

2. **Compass Service Layer** (`compass.py`): Converts raw axis data to heading using `atan2(Y, X) * (180/π)` normalized to 0–360°. Computes temperature from TOUT registers. Detects overflow (OVL flag), data-ready (DRDY flag), and all-zero conditions.

3. **gRPC Server Layer** (`server.py`): Implements all four RPCs. GetHeading and GetRawAxes do single reads. StreamHeadings runs a timed loop. GetStatus checks device connectivity and health.

## Key Decisions

- **Python over Go/C#**: Simplest I2C integration via smbus2; grpcio is mature for Python; development speed prioritized for hardware service.
- **smbus2 over direct ioctl**: smbus2 provides clean Pythonic API; well-tested with Raspberry Pi I2C.
- **atan2 heading**: Standard trigonometric approach; no tilt compensation (magnetometer only).
- **Graceful degradation**: All I2C reads wrapped in try/except; service stays up even with no sensor. Status RPC reports "unavailable" when sensor not found, "degraded" when all-zero data detected.
- **Environment variables**: Simple configuration approach suitable for Docker deployment.
- **Host network mode**: Required for gRPC service discovery in zSCOUT stack.

## Risks

- **No real hardware in CI**: Unit tests must use mocked smbus2. Integration testing requires physical Raspberry Pi with QMC5883L.
- **Magnetic interference**: Heading accuracy depends on environment; out of scope for this service (consumer responsibility).
- **I2C bus contention**: Single service owns the device, so no bus contention expected. Lock not needed.
