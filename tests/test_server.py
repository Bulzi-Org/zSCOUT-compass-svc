"""Unit tests for HTTP REST+SSE server endpoints."""

import json
import socket
import threading
import time
import urllib.request
import pytest

from compass_svc.i2c_driver import STATUS_DRDY


class TestGetStatus:
	def test_returns_healthy_status(self, test_client):
		response = test_client.get("/api/status")

		assert response.status_code == 200
		data = response.json()
		assert data["status"] == "healthy"
		assert data["deviceAddress"] == "0x0d"
		assert data["i2cBus"] == 1
		assert data["deviceFound"] is True
		assert data["overflow"] is False
		assert "timestamp" in data


class TestGetHeading:
	def test_returns_heading(self, test_client):
		response = test_client.get("/api/heading")

		assert response.status_code == 200
		data = response.json()
		assert 0.0 <= data["headingDegrees"] < 360.0
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
		assert data["statusRegister"] == f"0x{STATUS_DRDY:02x}"
		assert "timestamp" in data


class TestStreamHeadings:
	def test_stream_returns_sse_events(self, compass_service):
		"""Verify the SSE endpoint streams heading events via a live server."""
		import uvicorn
		from compass_svc.server import create_app

		app = create_app(compass_service)

		# Find a free port
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind(("127.0.0.1", 0))
			port = s.getsockname()[1]

		config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
		server = uvicorn.Server(config)
		t = threading.Thread(target=server.run, daemon=True)
		t.start()

		# Wait for server to accept connections
		for _ in range(50):
			try:
				with socket.create_connection(("127.0.0.1", port), timeout=0.1):
					break
			except OSError:
				time.sleep(0.1)

		try:
			events = []
			resp = urllib.request.urlopen(
				f"http://127.0.0.1:{port}/api/stream/headings?intervalMs=10",
				timeout=5,
			)
			for _ in range(200):  # safety limit
				line = resp.readline().decode().strip()
				if line.startswith("data:"):
					events.append(json.loads(line[len("data:"):]))
				if len(events) >= 3:
					break
			resp.close()
		finally:
			server.should_exit = True
			t.join(timeout=3)

		assert len(events) >= 3
		for event in events[:3]:
			assert 0.0 <= event["headingDegrees"] < 360.0
			assert event["x"] == 100
			assert event["y"] == 200
			assert event["z"] == 300
			assert "temperature" in event
			assert event["timestamp"] != ""
