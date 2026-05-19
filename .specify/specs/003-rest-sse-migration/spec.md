# Specification: Migrate from gRPC to HTTP REST+SSE API

**Issue**: #3 — feat: Migrate from gRPC to HTTP REST+SSE API
**Status**: Draft
**Author**: SpecKit Agent

## Summary

Replace the gRPC server (port 5100) with HTTP REST endpoints and Server-Sent Events (SSE) for streaming. This aligns with the zSCOUT platform decision to use HTTP REST for all Tier 2 service APIs, eliminating native `protoc` build dependencies (which cause QEMU segfaults during arm64 cross-compilation) and enabling simpler debugging via `curl`.

## Architecture Context

The transport layer changes from gRPC to HTTP REST+SSE. The I2C driver and compass business logic layers remain unchanged.

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

## Functional Requirements

### FR-1: GET /api/status

Device health check endpoint. Returns JSON with status ("healthy"/"degraded"/"unavailable"), device address, I2C bus, device_found flag, overflow flag, and ISO 8601 timestamp.

### FR-2: GET /api/heading

Current heading snapshot. Returns JSON with heading_degrees (0–360), raw x/y/z, temperature, overflow flag, and ISO 8601 timestamp.

### FR-3: GET /api/axes

Raw axis values. Returns JSON with x, y, z, status_register (hex string), and ISO 8601 timestamp.

### FR-4: GET /api/stream/headings (SSE)

Server-Sent Events stream of continuous heading updates. Event type: "heading". Data payload matches the heading response JSON. Supports `?interval_ms=N` query parameter (default: 100ms).

### FR-5: Dependency Removal

Remove `grpcio`, `grpcio-tools`, and `protobuf` from project dependencies. Remove `src/proto/` directory and `src/compass_svc/generated/` directory. Add `fastapi`, `uvicorn`, and `sse-starlette` as dependencies.

### FR-6: Dockerfile Update

Remove protoc code generation step. Remove gcc/python3-dev build dependencies that were needed only for gRPC native compilation. Replace `GRPC_PORT` env var with `HTTP_PORT`.

## Non-Functional Requirements

### NFR-1: Port Compatibility

Keep the same default port (5100) for backward-compatible deployment.

### NFR-2: Graceful Degradation

All REST endpoints must return valid JSON even when the sensor is unavailable. Status endpoint returns "unavailable", heading returns 0.

### NFR-3: ARM64 Deployment

Docker image must build for ARM64 without QEMU segfaults (the primary motivation for this migration).

### NFR-4: Test Coverage

All existing test scenarios must be preserved with equivalent REST/HTTP test coverage.

### NFR-5: SSE Reliability

SSE stream must handle client disconnects cleanly without resource leaks.

## Acceptance Criteria

- [ ] gRPC server replaced with HTTP REST endpoints
- [ ] `GET /api/status` returns JSON device health
- [ ] `GET /api/heading` returns current heading snapshot
- [ ] `GET /api/axes` returns raw axis values
- [ ] `GET /api/stream/headings` returns SSE stream of heading updates
- [ ] `grpcio`, `grpcio-tools`, `protobuf` removed from dependencies
- [ ] Proto files and generated code removed
- [ ] Dockerfile no longer runs protoc code generation
- [ ] All existing tests updated for REST endpoints
- [ ] Docker image builds successfully for arm64
- [ ] README updated with new REST API documentation
