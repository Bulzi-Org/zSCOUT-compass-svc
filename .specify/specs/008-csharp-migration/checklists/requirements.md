# Requirements Checklist: C# Migration (#8)

- [ ] REQ-001: All four endpoints return identical JSON schema to Python version
- [ ] REQ-002: System.Device.Gpio I2cDevice reads QMC5883L correctly
- [ ] REQ-003: Heading calculation matches Python (atan2(y,x), 0-360°)
- [ ] REQ-004: Status determination (healthy/degraded/unavailable) matches Python
- [ ] REQ-005: Graceful degradation — no crash when I2C device absent
- [ ] REQ-006: All env vars configurable (I2C_BUS, I2C_ADDRESS, HTTP_PORT, STREAM_INTERVAL_MS)
- [ ] REQ-007: Dockerfile builds with .NET 10 multi-stage for ARM64
- [ ] REQ-008: Unit tests cover heading, temperature, status, endpoints, SSE
- [ ] REQ-009: Project structure matches specified layout
- [ ] REQ-010: CI/CD workflows updated for .NET
