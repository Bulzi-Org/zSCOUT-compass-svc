# zSCOUT Compass Hardware Service — Agent Guide

## Project summary

Tier 2 hardware service container that owns the QMC5883L magnetometer via I2C (`/dev/i2c-1`, address `0x0d`) and exposes compass heading data through an HTTP REST+SSE API on port 5100. Part of the zSCOUT three-tier architecture — all application containers consume heading data through this service's API rather than accessing I2C directly.

## Commands

- Build: `pip install -e .`
- Test: `pytest tests/`
- Run app: `python -m compass_svc`
- Lint/format: `python -m py_compile src/compass_svc/*.py`
- Container build: `docker build -f deploy/Dockerfile .`
- Smoke test: `curl http://localhost:5100/api/status`

## Tech stack

- Python 3.12, FastAPI, uvicorn, sse-starlette
- smbus2 for I2C access to QMC5883L magnetometer
- pytest, httpx for testing
- Docker (debian:bookworm-slim, ARM64 build), targets Raspberry Pi CM5

## Project structure

```text
src/
  compass_svc/
    __init__.py
    i2c_driver.py              # QMC5883L register-level I2C access
    compass.py                 # Heading calculation, temperature, status logic
    server.py                  # FastAPI HTTP REST+SSE server
    config.py                  # Environment variable configuration
    __main__.py                # Entry point
tests/
  conftest.py                  # Shared fixtures, mock I2C
  test_i2c_driver.py           # I2C driver unit tests
  test_compass.py              # Heading calculation, edge cases
  test_server.py               # REST+SSE endpoint tests
deploy/
  Dockerfile                   # ARM64 build
  docker-compose.yml           # Service definition with device mapping
.github/
  workflows/
    publish.yml                # GHCR publish on push to main / tags
.specify/
  specs/                       # SpecKit specification artifacts
pyproject.toml                 # Project metadata, dependencies
```

## Architecture rules

- Keep transport layers thin: FastAPI endpoints delegate to CompassService.
- Keep business logic in compass.py, not in server.py or i2c_driver.py.
- Isolate I2C hardware access behind i2c_driver.py interface.
- Handle I2C failures explicitly — never crash, return degraded/unavailable status.
- Single service owns the QMC5883L device — no bus contention management needed.

## Code style

- Tab indentation for Python code.
- Use type hints on all function signatures.
- Use dataclasses for structured data (RawReading, HeadingData).
- Use structured logging with `logging` module.
- Keep public APIs documented with docstrings.
- Prefer `try/except` with specific error handling over broad catches where feasible.

## Rules

- Always use the SpecKit workflow and commit on each completed step for all new code changes.
- Never commit secrets, `.env` files, or hardcoded credentials.
- Docker images must target ARM64 for CM5 deployment.
- Generated protobuf code (compass_pb2.py, compass_pb2_grpc.py) must be committed to the repo.
- After regenerating protobuf, fix the import in compass_pb2_grpc.py to use `from compass_svc.generated import compass_pb2`.
- Reference hardware spec IDs in doc comments when implementing spec requirements.
- Environment variables for configuration: I2C_BUS, I2C_ADDRESS, HTTP_PORT.

## Testing

- Test framework: pytest
- Test command: `pytest tests/`
- Unit tests mock smbus2 for I2C — no hardware required.
- Test heading calculation edge cases (0°, 90°, 180°, 270°).
- Test overflow detection and all-zero detection.
- Test REST endpoints with mocked I2C layer.

## Git workflow

- Branch from `main`.
- Use conventional commit messages: `feat:`, `fix:`, `chore:`, `docs:`, `test:`
- Do not commit directly to `main`.
- Verify `pytest tests/` passes before pushing.

## Done criteria

A change is done when all are true:

- Requirements are implemented and documented.
- Tests are added/updated and passing.
- Build/lint/type checks are passing.
- PR is reviewed and merged.
