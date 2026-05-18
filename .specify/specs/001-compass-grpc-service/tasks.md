# Tasks: Compass Hardware Service

**Issue**: #1
**Plan**: `plan.md`

## Task List

### T1: Project Scaffolding
**Depends on**: none
- Create `pyproject.toml` with project metadata and dependencies (grpcio, grpcio-tools, smbus2, protobuf)
- Create dev dependencies (pytest, grpcio-testing)
- Create directory structure: `src/compass_svc/`, `src/proto/`, `tests/`, `deploy/`
- Add `__init__.py` files
- Update `.gitignore` for Python artifacts and generated protobuf code

### T2: Protobuf Definition and Code Generation
**Depends on**: T1
- Create `src/proto/compass.proto` matching the issue spec exactly
- Set up protoc generation command/script
- Generate `compass_pb2.py` and `compass_pb2_grpc.py` into `src/compass_svc/generated/`

### T3: I2C Driver Module
**Depends on**: T1
- Create `src/compass_svc/i2c_driver.py`
- QMC5883L register constants (XOUT, YOUT, ZOUT, STATUS, TOUT, CTRL1)
- CTRL1 configuration: continuous mode, 200Hz ODR, 8G range, 512 OSR
- Read raw axis data (16-bit signed, LSB first)
- Read status register (DRDY, OVL, DOR flags)
- Read temperature register
- Device detection (try read, return bool)
- All I2C access wrapped in try/except for graceful degradation

### T4: Compass Service Logic
**Depends on**: T3
- Create `src/compass_svc/compass.py`
- Heading calculation: `atan2(Y, X) * (180/π)` normalized to 0–360°
- Temperature conversion from raw TOUT value
- Status determination: healthy / degraded / unavailable
- All-zero axis detection → degraded
- Overflow detection from OVL flag

### T5: gRPC Server Implementation
**Depends on**: T2, T4
- Create `src/compass_svc/server.py`
- Implement GetHeading: single snapshot read
- Implement StreamHeadings: timed loop with configurable interval (default 100ms)
- Implement GetRawAxes: raw XYZ + status register
- Implement GetStatus: device availability, health status
- Create `src/compass_svc/__main__.py` entry point

### T6: Configuration Module
**Depends on**: T1
- Create `src/compass_svc/config.py`
- I2C_BUS (default: 1)
- I2C_ADDRESS (default: 0x0d)
- GRPC_PORT (default: 5100)
- STREAM_INTERVAL_MS (default: 100)

### T7: Dockerfile
**Depends on**: T5
- Create `deploy/Dockerfile`
- Base: debian:bookworm-slim
- Install Python 3, pip, i2c-tools, build dependencies
- Copy source, install dependencies
- Expose port 5100
- CMD runs gRPC server
- Must work on ARM64

### T8: Docker Compose
**Depends on**: T7
- Create `deploy/docker-compose.yml`
- Service: compass-svc
- Image: ghcr.io/bulzi-org/zscout-compass-svc:latest
- host network mode
- Device: /dev/i2c-1
- Environment variables

### T9: Unit Tests
**Depends on**: T5
- Create `tests/conftest.py` with mock I2C fixtures
- Create `tests/test_i2c_driver.py` — mocked register reads
- Create `tests/test_compass.py` — heading calculation (0°, 90°, 180°, 270°, negative normalization), overflow detection, all-zero detection
- Create `tests/test_server.py` — gRPC endpoint tests with mock I2C

### T10: GHCR Publish Workflow
**Depends on**: T7
- Create `.github/workflows/publish.yml`
- Trigger on push to main and version tags
- Build Docker image for ARM64
- Push to ghcr.io/bulzi-org/zscout-compass-svc

### T11: Update AGENTS.md
**Depends on**: T5
- Replace template content with actual project details
- Update commands, tech stack, project structure, rules

### T12: Update README.md
**Depends on**: T8
- Replace template content with project description
- Add build, test, run, and Docker instructions
- Document gRPC API endpoints
- Document environment variables
