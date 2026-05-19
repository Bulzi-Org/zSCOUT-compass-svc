# Tasks: Migrate from gRPC to HTTP REST+SSE API

**Issue**: #3
**Plan**: `003-rest-sse-migration/plan.md`

## Task Order (dependency-ordered)

### T1: Update dependencies in pyproject.toml
**Depends on**: None
Remove grpcio, grpcio-tools, protobuf from dependencies. Remove grpcio-testing and pytest-asyncio from dev dependencies. Add fastapi, uvicorn[standard], sse-starlette. Add httpx to dev dependencies. Update project description.

### T2: Rewrite server.py with FastAPI endpoints
**Depends on**: T1
Replace the gRPC CompassServicer class with a FastAPI application. Implement GET /api/status, GET /api/heading, GET /api/axes, and GET /api/stream/headings (SSE). Use create_app() factory pattern and serve() function for uvicorn startup.

### T3: Update config.py
**Depends on**: None
Rename GRPC_PORT to HTTP_PORT (same default 5100).

### T4: Rewrite __main__.py entry point
**Depends on**: T2, T3
Replace gRPC server startup with uvicorn.run(). Remove gRPC-specific signal handling (uvicorn handles graceful shutdown).

### T5: Remove proto files and generated code
**Depends on**: T2
Delete src/proto/ directory and src/compass_svc/generated/ directory.

### T6: Update test fixtures (conftest.py)
**Depends on**: T1
Remove gRPC imports from conftest.py. Keep mock I2C fixtures unchanged.

### T7: Rewrite test_server.py for REST endpoints
**Depends on**: T2, T6
Replace gRPC channel/stub tests with FastAPI TestClient tests. Cover all 4 endpoints including SSE streaming. Preserve equivalent test scenarios from existing gRPC tests.

### T8: Update Dockerfile
**Depends on**: T1, T5
Remove gcc, python3-dev apt packages. Remove grpc_tools.protoc step. Replace GRPC_PORT env var with HTTP_PORT. Remove COPY of proto files.

### T9: Update docker-compose.yml
**Depends on**: T3
Replace GRPC_PORT environment variable with HTTP_PORT.

### T10: Update README.md
**Depends on**: T2
Replace gRPC API documentation with REST+SSE endpoint docs. Update quick start to remove protoc steps. Update architecture diagram.

### T11: Update AGENTS.md
**Depends on**: T2
Update commands, tech stack, project structure, and smoke test command.

### T12: Update __init__.py
**Depends on**: None
Update module docstring from "gRPC API" to "REST API".

### T13: Verify and fix
**Depends on**: All above
Run pytest, py_compile, Docker build. Fix any issues.
