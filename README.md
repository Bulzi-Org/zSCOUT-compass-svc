# zSCOUT Compass Hardware Service

Tier 2 hardware service container that owns the QMC5883L magnetometer via I2C and exposes compass heading data through an HTTP REST+SSE API on port 5100.

## Architecture

```
Host OS (Tier 1) → /dev/i2c-1 (I2C bus)
    │
    ▼ --device /dev/i2c-1
zSCOUT-compass-svc (Tier 2) → HTTP REST+SSE :5100
    │
    ├── zscout-scanner (needs heading for direction-of-arrival)
    ├── zscout-hw-test (validates compass hardware)
    └── zscout-config-agent (status/config)
```

## REST+SSE API (port 5100)

### `GET /api/status`

Device health check.

```json
{
  "status": "healthy",
  "deviceAddress": "0x0d",
  "i2cBus": 1,
  "deviceFound": true,
  "overflow": false,
  "timestamp": "2026-05-19T05:30:00.0000000Z"
}
```

### `GET /api/heading`

Current heading snapshot.

```json
{
  "headingDegrees": 127.4,
  "x": 1234,
  "y": -567,
  "z": 890,
  "temperature": 23.5,
  "overflow": false,
  "timestamp": "2026-05-19T05:30:00.0000000Z"
}
```

### `GET /api/axes`

Raw axis values.

```json
{
  "x": 1234,
  "y": -567,
  "z": 890,
  "statusRegister": "0x01",
  "timestamp": "2026-05-19T05:30:00.0000000Z"
}
```

### `GET /api/stream/headings` (SSE)

Server-Sent Events stream of continuous heading updates.

Query parameter: `?intervalMs=100` (default: 100ms, min: 10ms, max: 10000ms)

```
event: heading
data: {"headingDegrees": 127.4, "x": 1234, "y": -567, "z": 890, "temperature": 23.5, "timestamp": "..."}

event: heading
data: {"headingDegrees": 128.1, ...}
```

## Quick Start

### Local Development

```bash
# Build
dotnet build zSCOUT-compass-svc.slnx

# Run tests (no hardware required — uses mock I2C)
dotnet test zSCOUT-compass-svc.slnx

# Run the service (requires /dev/i2c-1 or runs in degraded mode)
dotnet run --project src/ZScout.CompassSvc

# Test with curl
curl http://localhost:5100/api/status
curl http://localhost:5100/api/heading
curl http://localhost:5100/api/axes
curl -N "http://localhost:5100/api/stream/headings?intervalMs=500"
```

### Docker

```bash
# Build
docker build -f deploy/Dockerfile -t zscout-compass-svc .

# Run (with I2C device access)
docker run --rm --device /dev/i2c-1 -e HTTP_PORT=5100 zscout-compass-svc
```

### Docker Compose

```bash
docker compose -f deploy/docker-compose.yml up
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `I2C_BUS` | `1` | I2C bus number |
| `I2C_ADDRESS` | `0x0d` | QMC5883L I2C address |
| `HTTP_PORT` | `5100` | HTTP server port |
| `STREAM_INTERVAL_MS` | `100` | Default streaming interval (ms) |

## Hardware

- **Sensor**: QMC5883L 3-axis magnetometer
- **Interface**: I2C at address 0x0d on bus 1
- **Configuration**: Continuous mode, 200Hz ODR, 8G range, 512 OSR
- **Heading**: `atan2(Y, X)` normalized to 0–360°

## Tech Stack

- **Language**: C# / .NET 10
- **Framework**: ASP.NET Core Minimal API
- **I2C Library**: System.Device.Gpio (System.Device.I2c)
- **Testing**: xUnit, Moq, WebApplicationFactory
- **Docker**: debian:bookworm-slim, ARM64 target

## CI/CD

Two GitHub Actions workflows automate testing, image builds, and publishing.

### CI (`.github/workflows/ci.yml`)

Runs on **every push to `main`** and **every pull request** targeting `main`.

1. **test** — Sets up .NET 10, restores, builds, and runs `dotnet test`.
2. **docker-build** — After tests pass, builds the ARM64 Docker image via QEMU and Buildx **without pushing**.

### Publish (`.github/workflows/publish.yml`)

Runs on **push to `main`** and **version tags** (`v*`).

Builds the ARM64 Docker image and pushes it to GHCR:

```
ghcr.io/bulzi-org/zscout-compass-svc
```

## Graceful Degradation

The service runs even without a connected sensor:
- **No sensor**: Status reports "unavailable", heading returns 0
- **All-zero data**: Status reports "degraded"
- **Overflow**: Status reports "degraded", overflow flag set in responses

## License

See [LICENSE](LICENSE).
