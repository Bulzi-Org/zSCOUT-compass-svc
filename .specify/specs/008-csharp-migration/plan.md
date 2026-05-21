# Implementation Plan: C# .NET 10 Migration (#8)

## Approach

Full rewrite — replace all Python source files with a C# .NET 10 Minimal API project mirroring existing architecture layers:

1. **I2C Driver** (`Qmc5883lDriver.cs`) — register-level access behind `IQmc5883lDriver`
2. **Business Logic** (`CompassService.cs`) — heading, temperature, status
3. **Background Polling** (`HeadingReaderService.cs`) — `IHostedService` reads I2C
4. **Cache/Fan-out** (`HeadingCache.cs`) — latest reading + SSE subscribers
5. **HTTP Transport** (`Program.cs`) — Minimal API endpoints

## File Changes

### New
- `zSCOUT-compass-svc.slnx`, C# source/test projects

### Modified
- `deploy/Dockerfile`, `deploy/docker-compose.yml`, CI workflows, AGENTS.md, README.md

### Deleted
- `src/compass_svc/`, `tests/` (Python), `pyproject.toml`
