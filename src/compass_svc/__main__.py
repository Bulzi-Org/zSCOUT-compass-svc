"""Entry point for the zSCOUT Compass Hardware Service."""

import logging
import signal
import sys

from compass_svc.config import I2C_BUS, I2C_ADDRESS, GRPC_PORT
from compass_svc.i2c_driver import QMC5883L
from compass_svc.compass import CompassService
from compass_svc.server import serve

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
	logger.info(
		"Starting zSCOUT Compass Service (bus=%d, addr=0x%02x, port=%d)",
		I2C_BUS,
		I2C_ADDRESS,
		GRPC_PORT,
	)

	driver = QMC5883L(bus_number=I2C_BUS, address=I2C_ADDRESS)
	compass = CompassService(driver)

	if not compass.initialize():
		logger.warning("Sensor not available — running in degraded mode")

	server = serve(compass, GRPC_PORT)

	def shutdown(signum, frame):
		logger.info("Shutting down...")
		server.stop(grace=5)
		compass.shutdown()
		sys.exit(0)

	signal.signal(signal.SIGTERM, shutdown)
	signal.signal(signal.SIGINT, shutdown)

	logger.info("Compass service ready")
	server.wait_for_termination()


if __name__ == "__main__":
	main()
