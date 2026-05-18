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

## CI/CD

Two GitHub Actions workflows automate testing, image builds, and publishing.

### CI (`.github/workflows/ci.yml`)

Runs on **every push to `main`** and **every pull request** targeting `main`.

1. **test** — Sets up Python 3.11, installs the package with dev dependencies, and runs `pytest`. Generated protobuf files are committed to the repo, so no codegen step is needed.
2. **docker-build** — After tests pass, builds the ARM64 Docker image via QEMU and Buildx (`deploy/Dockerfile`) **without pushing**. This catches Dockerfile, dependency, or build-context issues before merge.

### Publish (`.github/workflows/publish.yml`)

Runs on **push to `main`** and **version tags** (`v*`).

Builds the ARM64 Docker image and pushes it to GHCR:

```
ghcr.io/bulzi-org/zscout-compass-svc
```

Image tags produced:
- `main` — latest from the main branch
- `<semver>` / `<major>.<minor>` — from version tags (e.g. `v1.2.3` → `1.2.3`, `1.2`)
- `sha-<commit>` — every build

### Docker Image Details

- **Base**: `debian:bookworm-slim`
- **Platform**: `linux/arm64` (cross-built via QEMU on GitHub-hosted runners)
- **Build context**: repo root; Dockerfile at `deploy/Dockerfile`
- **Build-time steps**: installs Python 3.11, project dependencies, and runs `grpc_tools.protoc` to generate gRPC stubs inside the image
- **Runtime**: `python -m compass_svc` on port 5100

### Adding CI Checks

If you modify the Dockerfile, protobuf definitions, or Python dependencies, the CI workflow will automatically verify the Docker image still builds. No manual Docker build is required before opening a PR.

## Graceful Degradation

The service runs even without a connected sensor:
- **No sensor**: Status reports "unavailable", heading returns 0
- **All-zero data**: Status reports "degraded"
- **Overflow**: Status reports "degraded", overflow flag set in responses

## License

See [LICENSE](LICENSE).
