# zSCOUT Compass Hardware Service

Tier 2 hardware service container that owns the QMC5883L magnetometer via I2C and exposes compass heading data through a gRPC API on port 5100.

## Architecture

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

## gRPC API (port 5100)

| RPC | Type | Description |
|---|---|---|
| `GetHeading` | Unary | Current heading snapshot (0–360°), raw XYZ, temperature |
| `StreamHeadings` | Server stream | Continuous heading updates at configurable rate |
| `GetRawAxes` | Unary | Raw X, Y, Z axis values + status register |
| `GetStatus` | Unary | Device health check (healthy/degraded/unavailable) |

Proto definition: `src/proto/compass.proto`

## Quick Start

### Local Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Generate protobuf code
python -m grpc_tools.protoc \
    -Isrc/proto \
    --python_out=src/compass_svc/generated \
    --grpc_python_out=src/compass_svc/generated \
    src/proto/compass.proto

# Run tests (no hardware required — uses mock I2C)
pytest tests/

# Run the service (requires /dev/i2c-1 or runs in degraded mode)
python -m compass_svc
```

### Docker

```bash
# Build
docker build -f deploy/Dockerfile -t zscout-compass-svc .

# Run (with I2C device access)
docker run --rm --device /dev/i2c-1 -e GRPC_PORT=5100 zscout-compass-svc
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
| `GRPC_PORT` | `5100` | gRPC server port |
| `STREAM_INTERVAL_MS` | `100` | Default streaming interval (ms) |

## Hardware

- **Sensor**: QMC5883L 3-axis magnetometer
- **Interface**: I2C at address 0x0d on bus 1
- **Configuration**: Continuous mode, 200Hz ODR, 8G range, 512 OSR
- **Heading**: `atan2(Y, X)` normalized to 0–360°

## Graceful Degradation

The service runs even without a connected sensor:
- **No sensor**: Status reports "unavailable", heading returns 0
- **All-zero data**: Status reports "degraded"
- **Overflow**: Status reports "degraded", overflow flag set in responses

## License

See [LICENSE](LICENSE).
