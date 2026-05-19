"""Unit tests for HTTP REST+SSE server endpoints."""

import json
import pytest

from compass_svc.i2c_driver import STATUS_DRDY


class TestGetStatus:
	def test_returns_healthy_status(self, test_client):
		response = test_client.get("/api/status")

		assert response.status_code == 200
		data = response.json()
		assert data["status"] == "healthy"
		assert data["device_address"] == "0x0d"
		assert data["i2c_bus"] == 1
		assert data["device_found"] is True
		assert data["overflow"] is False
		assert "timestamp" in data


class TestGetHeading:
	def test_returns_heading(self, test_client):
		response = test_client.get("/api/heading")

		assert response.status_code == 200
		data = response.json()
		assert 0.0 <= data["heading_degrees"] < 360.0
		assert data["x"] == 100
		assert data["y"] == 200
		assert data["z"] == 300
		assert "temperature" in data
		assert "overflow" in data
		assert data["timestamp"] != ""


class TestGetAxes:
	def test_returns_raw_values(self, test_client):
		response = test_client.get("/api/axes")

		assert response.status_code == 200
		data = response.json()
		assert data["x"] == 100
		assert data["y"] == 200
		assert data["z"] == 300
		assert data["status_register"] == f"0x{STATUS_DRDY:02x}"
		assert "timestamp" in data


class TestStreamHeadings:
	def test_stream_endpoint_registered(self, compass_service):
		"""Verify SSE stream route is registered in the FastAPI app."""
		from compass_svc.server import create_app

		app = create_app(compass_service)
		route_paths = [route.path for route in app.routes]
		assert "/api/stream/headings" in route_paths

	def test_stream_heading_data_format(self, compass_service):
		"""Test the heading data format that SSE would emit."""
		# Verify the heading data can be serialized correctly for SSE
		data = compass_service.read_heading()
		payload = {
			"heading_degrees": data.heading_degrees,
			"x": data.x_raw,
			"y": data.y_raw,
			"z": data.z_raw,
			"temperature": data.temperature_celsius,
			"timestamp": data.timestamp_utc,
		}
		# Verify it's JSON-serializable
		serialized = json.dumps(payload)
		parsed = json.loads(serialized)

		assert 0.0 <= parsed["heading_degrees"] < 360.0
		assert parsed["x"] == 100
		assert parsed["y"] == 200
		assert parsed["z"] == 300
		assert "temperature" in parsed
		assert parsed["timestamp"] != ""
