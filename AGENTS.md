# zSCOUT Compass Hardware Service — Agent Guide

## Project summary

Tier 2 hardware service container that owns the QMC5883L magnetometer via I2C (`/dev/i2c-1`, address `0x0d`) and exposes compass heading data through an HTTP REST+SSE API on port 5100. Part of the zSCOUT three-tier architecture — all application containers consume heading data through this service's API rather than accessing I2C directly.

## Commands

- Build: `dotnet build zSCOUT-compass-svc.slnx`
- Test: `dotnet test zSCOUT-compass-svc.slnx`
- Run app: `dotnet run --project src/ZScout.CompassSvc`
- Publish: `dotnet publish -c Release -o out src/ZScout.CompassSvc`
- Container build: `docker build -f deploy/Dockerfile .`
- Smoke test: `curl http://localhost:5100/api/status`

## Tech stack

- C# / .NET 10, ASP.NET Core Minimal API
- System.Device.Gpio (System.Device.I2c) for I2C access to QMC5883L magnetometer
- xUnit, Moq, Microsoft.AspNetCore.Mvc.Testing for testing
- Docker (debian:bookworm-slim, ARM64 build), targets Raspberry Pi CM5

## Project structure

```text
src/
  ZScout.CompassSvc/
    ZScout.CompassSvc.csproj       # Project file with System.Device.Gpio NuGet
    Program.cs                     # Minimal API setup, DI, endpoints
    Qmc5883lDriver.cs              # QMC5883L I2C driver + IQmc5883lDriver interface
    CompassService.cs              # Heading calculation, temperature, status logic
    HeadingCache.cs                # Channel<T> fan-out for SSE subscribers
    HeadingReaderService.cs        # IHostedService: continuous I2C polling
tests/
  ZScout.CompassSvc.Tests/
    ZScout.CompassSvc.Tests.csproj # Test project (xUnit, Moq)
    CompassServiceTests.cs         # Business logic unit tests
    EndpointTests.cs               # REST+SSE endpoint integration tests
deploy/
  Dockerfile                       # ARM64 multi-stage build
  docker-compose.yml               # Service definition with device mapping
.github/
  workflows/
    ci.yml                         # .NET build/test + Docker build on PR
    publish.yml                    # GHCR publish on push to main / tags
.specify/
  specs/                           # SpecKit specification artifacts
zSCOUT-compass-svc.slnx           # XML solution file
```

## Architecture rules

- Keep transport layers thin: Minimal API endpoints delegate to CompassService.
- Keep business logic in CompassService.cs, not in Program.cs or Qmc5883lDriver.cs.
- Isolate I2C hardware access behind IQmc5883lDriver interface.
- Handle I2C failures explicitly — never crash, return degraded/unavailable status.
- Single service owns the QMC5883L device — no bus contention management needed.

## Code style

- Tab indentation for C# code.
- Use type annotations on all method signatures (nullable reference types enabled).
- Use records for structured data (RawReading, HeadingData).
- Use structured logging with `ILogger<T>`.
- Keep public APIs documented with XML doc comments.
- Prefer specific exception handling over broad catches where feasible.

## Rules

- Always use the SpecKit workflow and commit on each completed step for all new code changes.
- Never commit secrets, `.env` files, or hardcoded credentials.
- Docker images must target ARM64 for CM5 deployment.
- Reference hardware spec IDs in doc comments when implementing spec requirements.
- Environment variables for configuration: I2C_BUS, I2C_ADDRESS, HTTP_PORT, STREAM_INTERVAL_MS.

## Testing

- Test framework: xUnit + Moq
- Test command: `dotnet test zSCOUT-compass-svc.slnx`
- Unit tests mock IQmc5883lDriver for I2C — no hardware required.
- Test heading calculation edge cases (0°, 90°, 180°, 270°).
- Test overflow detection and all-zero detection.
- Test REST endpoints with WebApplicationFactory and mocked I2C layer.

## Git workflow

- Branch from `main`.
- **Worktrees** must be created in `~/GitHub/Bulzi-Org/zSCOUT/worktrees/` — NEVER in the repo root or submodule directories. Naming: `<repo-short>-<type><issue>` (e.g. `gps-svc-fix40`)
- Use conventional commit messages: `feat:`, `fix:`, `chore:`, `docs:`, `test:`
- Do not commit directly to `main`.
- Verify `dotnet test` passes before pushing.

## Done criteria

A change is done when all are true:

- Requirements are implemented and documented.
- Tests are added/updated and passing.
- Build/lint/type checks are passing.
- PR is reviewed and merged.


## Parent Project Rules

This repository is a submodule of the zSCOUT parent project at `~/GitHub/Bulzi-Org/zSCOUT/`.
Before starting any work, read and follow the project-wide rules in the parent repository:

**File:** `../AGENTS.md` (or `~/GitHub/Bulzi-Org/zSCOUT/AGENTS.md`)

The parent AGENTS.md contains critical instructions for:
- Kanban board updates (project board status transitions)
- WSL working directory requirements
- Cross-repo orchestration conventions

These parent rules apply to ALL zSCOUT submodule repositories and must be followed in addition to this file's repo-specific rules.

## Agent execution mode

Always use interactive VS Code agent chat tabs for sub-agents.
Do not use background/headless task agents.
If interactive tabs are unavailable, stop and report that instead of falling back.
