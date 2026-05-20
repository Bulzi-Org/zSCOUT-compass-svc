"""Compass service logic — heading calculation, temperature, and status."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

from compass_svc.i2c_driver import QMC5883L, RawReading, STATUS_DRDY, STATUS_OVL, STATUS_DOR

logger = logging.getLogger(__name__)


@dataclass
class HeadingData:
	"""Processed heading data from the compass sensor."""

	heading_degrees: float = 0.0
	x_raw: int = 0
	y_raw: int = 0
	z_raw: int = 0
	temperature_celsius: float = 0.0
	overflow: bool = False
	data_ready: bool = False
	data_overrun: bool = False
	timestamp_utc: str = ""
	status: str = "unavailable"


def calculate_heading(x: int, y: int) -> float:
	"""Calculate heading in degrees (0–360) from raw X and Y axis values.

	Uses atan2(Y, X) and normalizes the result to 0–360°.
	"""
	heading_rad = math.atan2(y, x)
	heading_deg = math.degrees(heading_rad)
	# Normalize to 0–360
	if heading_deg < 0:
		heading_deg += 360.0
	return heading_deg


def convert_temperature(raw: int) -> float:
	"""Convert raw temperature register value to Celsius.

	The QMC5883L temperature output is relative, with ~100 LSB/°C.
	We return a relative value; absolute calibration depends on the chip.
	"""
	return raw / 100.0


def determine_status(reading: RawReading, device_found: bool) -> str:
	"""Determine sensor health status.

	Returns:
		"healthy" — device found, data is valid
		"degraded" — device found but data is all zeros or overflow
		"unavailable" — device not found or communication error
	"""
	if not device_found:
		return "unavailable"

	# All-zero detection
	if reading.x == 0 and reading.y == 0 and reading.z == 0:
		return "degraded"

	# Overflow detection
	if reading.status & STATUS_OVL:
		return "degraded"

	return "healthy"


class CompassService:
	"""High-level compass service wrapping the I2C driver."""

	def __init__(self, driver: QMC5883L) -> None:
		self._driver = driver

	@property
	def driver(self) -> QMC5883L:
		return self._driver

	def initialize(self) -> bool:
		"""Initialize the sensor. Returns True if successful."""
		return self._driver.open()

	def shutdown(self) -> None:
		"""Shut down the sensor connection."""
		self._driver.close()

	def read_heading(self) -> HeadingData:
		"""Read current heading data from the sensor."""
		reading = self._driver.read()
		status = determine_status(reading, self._driver.device_found)
		timestamp = datetime.now(timezone.utc).isoformat()

		heading_deg = 0.0
		if status != "unavailable" and not (reading.x == 0 and reading.y == 0):
			heading_deg = calculate_heading(reading.x, reading.y)

		return HeadingData(
			heading_degrees=heading_deg,
			x_raw=reading.x,
			y_raw=reading.y,
			z_raw=reading.z,
			temperature_celsius=convert_temperature(reading.temperature_raw),
			overflow=bool(reading.status & STATUS_OVL),
			data_ready=bool(reading.status & STATUS_DRDY),
			data_overrun=bool(reading.status & STATUS_DOR),
			timestamp_utc=timestamp,
			status=status,
		)

	def read_raw_axes(self) -> tuple[int, int, int, int]:
		"""Read raw axis values and status register.

		Returns:
			Tuple of (x, y, z, status_register)
		"""
		reading = self._driver.read()
		return reading.x, reading.y, reading.z, reading.status

	def get_status(self) -> dict:
		"""Get device status information."""
		reading = self._driver.read()
		status = determine_status(reading, self._driver.device_found)

		return {
			"deviceFound": self._driver.device_found,
			"i2cBus": str(self._driver.bus_number),
			"deviceAddress": f"0x{self._driver.address:02x}",
			"dataAvailable": bool(reading.status & STATUS_DRDY),
			"overflow": bool(reading.status & STATUS_OVL),
			"status": status,
		}
