"""Entry point for the zSCOUT Compass Hardware Service."""

import logging

from compass_svc.config import I2C_BUS, I2C_ADDRESS, HTTP_PORT
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
		HTTP_PORT,
	)

	driver = QMC5883L(bus_number=I2C_BUS, address=I2C_ADDRESS)
	compass = CompassService(driver)

	if not compass.initialize():
		logger.warning("Sensor not available — running in degraded mode")

	serve(compass, HTTP_PORT)


if __name__ == "__main__":
	main()
