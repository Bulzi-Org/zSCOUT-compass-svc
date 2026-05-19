"""HTTP REST+SSE server implementation for the Compass service."""

import asyncio
import json
import logging
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI, Query
from sse_starlette.sse import EventSourceResponse

from compass_svc.compass import CompassService

logger = logging.getLogger(__name__)


def create_app(compass: CompassService) -> FastAPI:
	"""Create the FastAPI application with compass endpoints."""
	app = FastAPI(
		title="zSCOUT Compass Service",
		description="QMC5883L magnetometer REST+SSE API",
		version="0.2.0",
	)

	@app.get("/api/status")
	def get_status() -> dict:
		"""Device health check."""
		status_info = compass.get_status()
		reading = compass.driver.read()
		from compass_svc.i2c_driver import STATUS_OVL
		return {
			"status": status_info["status"],
			"device_address": status_info["device_address"],
			"i2c_bus": int(status_info["i2c_bus"]),
			"device_found": status_info["device_found"],
			"overflow": bool(reading.status & STATUS_OVL),
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	@app.get("/api/heading")
	def get_heading() -> dict:
		"""Current heading snapshot."""
		data = compass.read_heading()
		return {
			"heading_degrees": data.heading_degrees,
			"x": data.x_raw,
			"y": data.y_raw,
			"z": data.z_raw,
			"temperature": data.temperature_celsius,
			"overflow": data.overflow,
			"timestamp": data.timestamp_utc,
		}

	@app.get("/api/axes")
	def get_axes() -> dict:
		"""Raw axis values."""
		x, y, z, status_reg = compass.read_raw_axes()
		return {
			"x": x,
			"y": y,
			"z": z,
			"status_register": f"0x{status_reg:02x}",
			"timestamp": datetime.now(timezone.utc).isoformat(),
		}

	@app.get("/api/stream/headings")
	async def stream_headings(
		interval_ms: int = Query(default=100, ge=10, le=10000),
	) -> EventSourceResponse:
		"""SSE stream of continuous heading updates."""
		interval_sec = interval_ms / 1000.0

		async def event_generator():
			try:
				while True:
					data = compass.read_heading()
					payload = json.dumps({
						"heading_degrees": data.heading_degrees,
						"x": data.x_raw,
						"y": data.y_raw,
						"z": data.z_raw,
						"temperature": data.temperature_celsius,
						"timestamp": data.timestamp_utc,
					})
					yield {"event": "heading", "data": payload}
					await asyncio.sleep(interval_sec)
			except asyncio.CancelledError:
				logger.debug("SSE stream cancelled by client disconnect")

		return EventSourceResponse(event_generator())

	return app


def serve(compass: CompassService, port: int) -> None:
	"""Start the HTTP server with uvicorn."""
	app = create_app(compass)
	logger.info("Starting HTTP server on port %d", port)
	uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
