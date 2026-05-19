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
	def test_stream_returns_sse_events(self, test_client):
		with test_client.stream("GET", "/api/stream/headings?interval_ms=50") as response:
			assert response.status_code == 200
			assert "text/event-stream" in response.headers["content-type"]

			events = []
			for line in response.iter_lines():
				if line.startswith("data:"):
					payload = json.loads(line[len("data:"):].strip())
					events.append(payload)
					if len(events) >= 3:
						break

			assert len(events) == 3
			for event in events:
				assert 0.0 <= event["heading_degrees"] < 360.0
				assert "x" in event
				assert "y" in event
				assert "z" in event
				assert "timestamp" in event
