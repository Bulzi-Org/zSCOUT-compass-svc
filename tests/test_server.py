"""Unit tests for gRPC server endpoints."""

import pytest
from unittest.mock import MagicMock
from concurrent import futures

import grpc

from compass_svc.compass import CompassService
from compass_svc.i2c_driver import QMC5883L, STATUS_DRDY
from compass_svc.server import CompassServicer, serve
from compass_svc.generated import compass_pb2, compass_pb2_grpc
from tests.conftest import make_i2c_block_data


@pytest.fixture
def grpc_server_and_channel(driver_with_mock_bus):
	"""Start a gRPC server with mock I2C and return (channel, stub)."""
	compass = CompassService(driver_with_mock_bus)
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
	compass_pb2_grpc.add_CompassServiceServicer_to_server(
		CompassServicer(compass), server
	)
	port = server.add_insecure_port("[::]:0")
	server.start()

	channel = grpc.insecure_channel(f"localhost:{port}")
	stub = compass_pb2_grpc.CompassServiceStub(channel)

	yield stub

	channel.close()
	server.stop(grace=0)


class TestGetHeading:
	def test_returns_heading(self, grpc_server_and_channel):
		stub = grpc_server_and_channel
		response = stub.GetHeading(compass_pb2.GetHeadingRequest())

		assert 0.0 <= response.heading_degrees < 360.0
		assert response.x_raw == 100
		assert response.y_raw == 200
		assert response.z_raw == 300
		assert response.timestamp_utc != ""


class TestStreamHeadings:
	def test_stream_returns_updates(self, grpc_server_and_channel):
		stub = grpc_server_and_channel
		request = compass_pb2.StreamHeadingsRequest(interval_ms=50)

		updates = []
		for update in stub.StreamHeadings(request):
			updates.append(update)
			if len(updates) >= 3:
				break

		assert len(updates) == 3
		for i, update in enumerate(updates):
			assert 0.0 <= update.heading_degrees < 360.0
			assert update.sample_number == i + 1
			assert update.timestamp_utc != ""


class TestGetRawAxes:
	def test_returns_raw_values(self, grpc_server_and_channel):
		stub = grpc_server_and_channel
		response = stub.GetRawAxes(compass_pb2.GetRawAxesRequest())

		assert response.x_raw == 100
		assert response.y_raw == 200
		assert response.z_raw == 300
		assert response.status_register == STATUS_DRDY


class TestGetStatus:
	def test_returns_healthy_status(self, grpc_server_and_channel):
		stub = grpc_server_and_channel
		response = stub.GetStatus(compass_pb2.GetStatusRequest())

		assert response.device_found is True
		assert response.i2c_bus == "1"
		assert response.device_address == "0x0d"
		assert response.status == "healthy"
