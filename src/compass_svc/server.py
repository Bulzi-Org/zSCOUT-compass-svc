"""gRPC server implementation for the Compass service."""

import logging
import time
from concurrent import futures

import grpc

from compass_svc.compass import CompassService
from compass_svc.generated import compass_pb2, compass_pb2_grpc

logger = logging.getLogger(__name__)


class CompassServicer(compass_pb2_grpc.CompassServiceServicer):
	"""gRPC servicer for CompassService RPCs."""

	def __init__(self, compass: CompassService) -> None:
		self._compass = compass

	def GetHeading(self, request, context):
		"""Get current heading snapshot."""
		data = self._compass.read_heading()
		return compass_pb2.HeadingResponse(
			heading_degrees=data.heading_degrees,
			x_raw=data.x_raw,
			y_raw=data.y_raw,
			z_raw=data.z_raw,
			temperature_celsius=data.temperature_celsius,
			overflow=data.overflow,
			timestamp_utc=data.timestamp_utc,
		)

	def StreamHeadings(self, request, context):
		"""Stream continuous heading updates at configurable rate."""
		interval_ms = request.interval_ms if request.interval_ms > 0 else 100
		interval_sec = interval_ms / 1000.0
		sample_number = 0

		while context.is_active():
			data = self._compass.read_heading()
			sample_number += 1

			yield compass_pb2.HeadingUpdate(
				heading_degrees=data.heading_degrees,
				x_raw=data.x_raw,
				y_raw=data.y_raw,
				z_raw=data.z_raw,
				temperature_celsius=data.temperature_celsius,
				overflow=data.overflow,
				data_ready=data.data_ready,
				data_overrun=data.data_overrun,
				sample_number=sample_number,
				timestamp_utc=data.timestamp_utc,
			)

			time.sleep(interval_sec)

	def GetRawAxes(self, request, context):
		"""Get raw axis values for calibration."""
		x, y, z, status_reg = self._compass.read_raw_axes()
		return compass_pb2.RawAxesResponse(
			x_raw=x,
			y_raw=y,
			z_raw=z,
			status_register=status_reg,
		)

	def GetStatus(self, request, context):
		"""Health check."""
		status_info = self._compass.get_status()
		return compass_pb2.StatusResponse(
			device_found=status_info["device_found"],
			i2c_bus=status_info["i2c_bus"],
			device_address=status_info["device_address"],
			data_available=status_info["data_available"],
			status=status_info["status"],
		)


def serve(compass: CompassService, port: int) -> grpc.Server:
	"""Create and start the gRPC server."""
	server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
	compass_pb2_grpc.add_CompassServiceServicer_to_server(
		CompassServicer(compass), server
	)
	server.add_insecure_port(f"[::]:{port}")
	server.start()
	logger.info("gRPC server started on port %d", port)
	return server
