"""Shared test fixtures."""

import struct
import pytest
from unittest.mock import MagicMock, patch

from compass_svc.i2c_driver import QMC5883L, STATUS_DRDY


def make_i2c_block_data(x: int, y: int, z: int, status: int = STATUS_DRDY, temp: int = 2500) -> list[int]:
	"""Build a 9-byte I2C block read response matching QMC5883L register layout."""
	data = bytearray(9)
	struct.pack_into("<h", data, 0, x)
	struct.pack_into("<h", data, 2, y)
	struct.pack_into("<h", data, 4, z)
	data[6] = status
	struct.pack_into("<h", data, 7, temp)
	return list(data)


@pytest.fixture
def mock_smbus():
	"""Create a mock SMBus instance."""
	mock_bus = MagicMock()
	mock_bus.read_i2c_block_data.return_value = make_i2c_block_data(100, 200, 300)
	mock_bus.read_byte_data.return_value = STATUS_DRDY
	return mock_bus


@pytest.fixture
def driver_with_mock_bus(mock_smbus):
	"""Create a QMC5883L driver with a mocked SMBus."""
	driver = QMC5883L(bus_number=1, address=0x0d)
	with patch("compass_svc.i2c_driver.SMBus", return_value=mock_smbus):
		driver.open()
	# Replace the bus with our mock after open()
	driver._bus = mock_smbus
	driver._device_found = True
	return driver
