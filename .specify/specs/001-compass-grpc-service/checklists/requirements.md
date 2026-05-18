# Requirements Checklist

**Issue**: #1
**Spec**: `../spec.md`

## Functional Requirements

- [ ] FR-1: GetHeading returns heading (0–360°), raw XYZ, temperature, overflow, timestamp
- [ ] FR-2: StreamHeadings streams at configurable interval (default 100ms)
- [ ] FR-3: GetRawAxes returns raw XYZ and status register
- [ ] FR-4: GetStatus returns device_found, bus, address, data_available, health status

## Non-Functional Requirements

- [ ] NFR-1: Service does not crash when sensor missing/disconnected
- [ ] NFR-2: All-zero axis values detected → status "degraded"
- [ ] NFR-3: Overflow flag (OVL) monitored and reported
- [ ] NFR-4: Docker image builds for ARM64, no --privileged required
- [ ] NFR-5: I2C_BUS, I2C_ADDRESS, GRPC_PORT configurable via env vars

## Code Quality

- [ ] Protobuf definition matches issue spec exactly
- [ ] Unit tests cover heading calculation edge cases (0°, 90°, 180°, 270°)
- [ ] Unit tests cover overflow detection and all-zero detection
- [ ] gRPC endpoints tested with mocked I2C layer
- [ ] No hardcoded secrets or credentials
- [ ] Structured logging throughout
- [ ] README updated with build/run instructions
- [ ] AGENTS.md updated with actual project details

## Delivery

- [ ] All code compiles and tests pass
- [ ] Dockerfile builds successfully
- [ ] GHCR publish workflow configured
- [ ] PR created with conventional commit messages
