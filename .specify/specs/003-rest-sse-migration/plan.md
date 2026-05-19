# Implementation Plan: Migrate from gRPC to HTTP REST+SSE API

**Issue**: #3
**Spec**: `003-rest-sse-migration/spec.md`

## Approach

Replace the gRPC transport layer with FastAPI HTTP REST endpoints and SSE streaming. The I2C driver (`i2c_driver.py`) and business logic (`compass.py`) remain untouched — only the transport layer (`server.py`), entry point (`__main__.py`), configuration (`config.py`), tests, Dockerfile, and documentation change.

## Changes Overview

### 1. Dependencies (`pyproject.toml`)

**Remove**: `grpcio`, `grpcio-tools`, `protobuf`, `grpcio-testing`
**Add**: `fastapi>=0.115.0`, `uvicorn[standard]>=0.34.0`, `sse-starlette>=2.0.0`
**Dev add**: `httpx>=0.28.0` (for TestClient)
**Remove dev**: `pytest-asyncio`, `grpcio-testing`

### 2. Server Layer (`src/compass_svc/server.py`)

Replace `CompassServicer` (gRPC) with a FastAPI application:

- `GET /api/status` → calls `compass.get_status()`, adds overflow + timestamp
- `GET /api/heading` → calls `compass.read_heading()`, returns JSON
- `GET /api/axes` → calls `compass.read_raw_axes()`, returns JSON with hex status_register
- `GET /api/stream/headings` → SSE endpoint using `sse-starlette`, calls `compass.read_heading()` in a loop with configurable `interval_ms` query param

The `create_app(compass)` factory returns a FastAPI app. The `serve(compass, port)` function starts uvicorn programmatically.

### 3. Configuration (`src/compass_svc/config.py`)

- Rename `GRPC_PORT` → `HTTP_PORT` (same default: 5100)
- Keep `I2C_BUS`, `I2C_ADDRESS`, `STREAM_INTERVAL_MS`

### 4. Entry Point (`src/compass_svc/__main__.py`)

- Replace `server.wait_for_termination()` with `uvicorn.run()`
- Signal handling delegated to uvicorn

### 5. Proto / Generated Code Removal

- Delete `src/proto/` directory
- Delete `src/compass_svc/generated/` directory

### 6. Tests

Replace gRPC test fixtures with FastAPI `TestClient` (from `httpx`):

- `test_server.py`: Use `TestClient(app)` instead of gRPC channel/stub. Test all 4 endpoints + SSE streaming.
- `conftest.py`: Remove gRPC imports; keep mock I2C fixtures.
- `test_compass.py`, `test_i2c_driver.py`: No changes needed (no gRPC dependency).

### 7. Dockerfile

- Remove `gcc`, `python3-dev` apt packages (no native compilation needed)
- Remove `grpc_tools.protoc` step
- Replace `GRPC_PORT` env var with `HTTP_PORT`

### 8. Documentation

- `README.md`: Replace gRPC API table with REST+SSE endpoint docs, update quick start, remove protoc steps
- `AGENTS.md`: Update commands, tech stack, project structure
- `__init__.py`: Update module docstring

### 9. CI Workflow

- `ci.yml`: Remove any protoc/gRPC-specific steps (current CI relies on committed generated code, so minimal changes expected)

## Files Modified

- `pyproject.toml`
- `src/compass_svc/server.py` (rewritten)
- `src/compass_svc/config.py`
- `src/compass_svc/__main__.py`
- `src/compass_svc/__init__.py`
- `tests/conftest.py`
- `tests/test_server.py` (rewritten)
- `deploy/Dockerfile`
- `deploy/docker-compose.yml`
- `README.md`
- `AGENTS.md`

## Files Removed

- `src/proto/compass.proto`
- `src/compass_svc/generated/__init__.py`
- `src/compass_svc/generated/compass_pb2.py`
- `src/compass_svc/generated/compass_pb2_grpc.py`

## Files Unchanged

- `src/compass_svc/i2c_driver.py`
- `src/compass_svc/compass.py`
- `tests/test_compass.py`
- `tests/test_i2c_driver.py`
