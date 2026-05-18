"""QMC5883L magnetometer I2C driver using smbus2."""

import logging
import struct
from dataclasses import dataclass

try:
	from smbus2 import SMBus
except ImportError:
	SMBus = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

# QMC5883L register addresses
REG_XOUT_L = 0x00
REG_XOUT_H = 0x01
REG_YOUT_L = 0x02
REG_YOUT_H = 0x03
REG_ZOUT_L = 0x04
REG_ZOUT_H = 0x05
REG_STATUS = 0x06
REG_TOUT_L = 0x07
REG_TOUT_H = 0x08
REG_CTRL1 = 0x09
REG_CTRL2 = 0x0A
REG_SET_RESET = 0x0B

# STATUS register flags
STATUS_DRDY = 0x01  # Data Ready
STATUS_OVL = 0x02   # Overflow
STATUS_DOR = 0x04   # Data Overrun

# CTRL1 configuration
# Mode: Continuous (0b01), ODR: 200Hz (0b11 << 2), Range: 8G (0b01 << 4), OSR: 512 (0b00 << 6)
CTRL1_CONTINUOUS_200HZ_8G_512OSR = 0x1D


@dataclass
class RawReading:
	"""Raw sensor reading from QMC5883L."""

	x: int = 0
	y: int = 0
	z: int = 0
	status: int = 0
	temperature_raw: int = 0


class QMC5883L:
	"""Driver for QMC5883L magnetometer via I2C."""

	def __init__(self, bus_number: int, address: int) -> None:
		self._bus_number = bus_number
		self._address = address
		self._bus: SMBus | None = None
		self._device_found = False

	@property
	def bus_number(self) -> int:
		return self._bus_number

	@property
	def address(self) -> int:
		return self._address

	@property
	def device_found(self) -> bool:
		return self._device_found

	def open(self) -> bool:
		"""Open the I2C bus and initialize the sensor. Returns True if successful."""
		if SMBus is None:
			logger.error("smbus2 is not available")
			self._device_found = False
			return False

		try:
			self._bus = SMBus(self._bus_number)
			# Reset the chip
			self._bus.write_byte_data(self._address, REG_CTRL2, 0x80)
			# Recommended SET/RESET period
			self._bus.write_byte_data(self._address, REG_SET_RESET, 0x01)
			# Configure: continuous mode, 200Hz, 8G range, 512 OSR
			self._bus.write_byte_data(self._address, REG_CTRL1, CTRL1_CONTINUOUS_200HZ_8G_512OSR)
			self._device_found = True
			logger.info(
				"QMC5883L initialized on bus %d at address 0x%02x",
				self._bus_number,
				self._address,
			)
			return True
		except Exception:
			logger.exception("Failed to initialize QMC5883L")
			self._device_found = False
			return False

	def close(self) -> None:
		"""Close the I2C bus."""
		if self._bus is not None:
			try:
				self._bus.close()
			except Exception:
				logger.exception("Error closing I2C bus")
			self._bus = None

	def read(self) -> RawReading:
		"""Read all sensor data. Returns zero-filled reading on error."""
		if self._bus is None or not self._device_found:
			return RawReading()

		try:
			# Read 9 bytes starting from register 0x00 (X_L through TOUT_H)
			data = self._bus.read_i2c_block_data(self._address, REG_XOUT_L, 9)

			# 16-bit signed values, LSB first
			x = struct.unpack_from("<h", bytes(data), 0)[0]
			y = struct.unpack_from("<h", bytes(data), 2)[0]
			z = struct.unpack_from("<h", bytes(data), 4)[0]
			status = data[6]
			temperature_raw = struct.unpack_from("<h", bytes(data), 7)[0]

			return RawReading(
				x=x,
				y=y,
				z=z,
				status=status,
				temperature_raw=temperature_raw,
			)
		except Exception:
			logger.exception("Error reading QMC5883L")
			self._device_found = False
			return RawReading()

	def detect(self) -> bool:
		"""Try to detect the QMC5883L on the bus. Returns True if found."""
		if SMBus is None:
			return False

		try:
			bus = self._bus or SMBus(self._bus_number)
			bus.read_byte_data(self._address, REG_STATUS)
			if self._bus is None:
				bus.close()
			self._device_found = True
			return True
		except Exception:
			self._device_found = False
			return False
