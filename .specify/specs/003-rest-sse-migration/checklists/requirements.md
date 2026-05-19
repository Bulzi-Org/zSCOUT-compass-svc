# Requirements Checklist: REST+SSE Migration

**Issue**: #3
**Spec**: `003-rest-sse-migration/spec.md`

## Functional Requirements

- [ ] **FR-1**: GET /api/status returns JSON with status, device_address, i2c_bus, device_found, overflow, timestamp
- [ ] **FR-2**: GET /api/heading returns JSON with heading_degrees, x, y, z, temperature, overflow, timestamp
- [ ] **FR-3**: GET /api/axes returns JSON with x, y, z, status_register (hex), timestamp
- [ ] **FR-4**: GET /api/stream/headings returns SSE stream with event type "heading" and JSON data
- [ ] **FR-4a**: SSE endpoint supports ?interval_ms query parameter (default: 100ms)
- [ ] **FR-5**: grpcio, grpcio-tools, protobuf removed from dependencies
- [ ] **FR-5a**: src/proto/ directory removed
- [ ] **FR-5b**: src/compass_svc/generated/ directory removed
- [ ] **FR-5c**: fastapi, uvicorn, sse-starlette added as dependencies
- [ ] **FR-6**: Dockerfile no longer runs protoc or requires gcc/python3-dev for gRPC

## Non-Functional Requirements

- [ ] **NFR-1**: Default port remains 5100
- [ ] **NFR-2**: All endpoints return valid JSON when sensor is unavailable
- [ ] **NFR-3**: Docker image builds for ARM64
- [ ] **NFR-4**: All existing test scenarios have equivalent REST/HTTP coverage
- [ ] **NFR-5**: SSE stream handles client disconnects without resource leaks

## Documentation

- [ ] README updated with REST+SSE API documentation
- [ ] AGENTS.md updated with new commands and tech stack
- [ ] Quick start instructions updated (no protoc steps)

## Quality Gates

- [ ] pytest tests/ passes
- [ ] python -m py_compile on all source files passes
- [ ] Docker image builds successfully
