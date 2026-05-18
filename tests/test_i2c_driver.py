"""Unit tests for the QMC5883L I2C driver."""

from unittest.mock import MagicMock, patch

from compass_svc.i2c_driver import (
	QMC5883L,
	RawReading,
	REG_XOUT_L,
	REG_CTRL1,
	REG_CTRL2,
	REG_SET_RESET,
	CTRL1_CONTINUOUS_200HZ_8G_512OSR,
)
from tests.conftest import make_i2c_block_data


class TestQMC5883LInit:
	def test_open_success(self):
		mock_bus = MagicMock()
		driver = QMC5883L(bus_number=1, address=0x0d)

		with patch("compass_svc.i2c_driver.SMBus", return_value=mock_bus):
			result = driver.open()

		assert result is True
		assert driver.device_found is True
		# Verify initialization sequence: reset, set/reset, ctrl1
		mock_bus.write_byte_data.assert_any_call(0x0d, REG_CTRL2, 0x80)
		mock_bus.write_byte_data.assert_any_call(0x0d, REG_SET_RESET, 0x01)
		mock_bus.write_byte_data.assert_any_call(0x0d, REG_CTRL1, CTRL1_CONTINUOUS_200HZ_8G_512OSR)

	def test_open_failure(self):
		driver = QMC5883L(bus_number=1, address=0x0d)

		with patch("compass_svc.i2c_driver.SMBus", side_effect=OSError("No I2C bus")):
			result = driver.open()

		assert result is False
		assert driver.device_found is False

	def test_open_smbus_unavailable(self):
		driver = QMC5883L(bus_number=1, address=0x0d)

		with patch("compass_svc.i2c_driver.SMBus", None):
			result = driver.open()

		assert result is False
		assert driver.device_found is False


class TestQMC5883LRead:
	def test_read_success(self, driver_with_mock_bus):
		reading = driver_with_mock_bus.read()
		assert reading.x == 100
		assert reading.y == 200
		assert reading.z == 300
		assert reading.status == 0x01  # DRDY
		assert reading.temperature_raw == 2500

	def test_read_negative_values(self, driver_with_mock_bus, mock_smbus):
		mock_smbus.read_i2c_block_data.return_value = make_i2c_block_data(-500, -1000, -200)
		reading = driver_with_mock_bus.read()
		assert reading.x == -500
		assert reading.y == -1000
		assert reading.z == -200

	def test_read_when_not_initialized(self):
		driver = QMC5883L(bus_number=1, address=0x0d)
		reading = driver.read()
		assert reading == RawReading()

	def test_read_i2c_error_returns_zero(self, driver_with_mock_bus, mock_smbus):
		mock_smbus.read_i2c_block_data.side_effect = OSError("I2C error")
		reading = driver_with_mock_bus.read()
		assert reading == RawReading()
		assert driver_with_mock_bus.device_found is False

	def test_properties(self):
		driver = QMC5883L(bus_number=2, address=0x1e)
		assert driver.bus_number == 2
		assert driver.address == 0x1e
		assert driver.device_found is False


class TestQMC5883LDetect:
	def test_detect_success(self):
		mock_bus = MagicMock()
		driver = QMC5883L(bus_number=1, address=0x0d)

		with patch("compass_svc.i2c_driver.SMBus", return_value=mock_bus):
			result = driver.detect()

		assert result is True
		assert driver.device_found is True

	def test_detect_failure(self):
		driver = QMC5883L(bus_number=1, address=0x0d)

		with patch("compass_svc.i2c_driver.SMBus", side_effect=OSError("No device")):
			result = driver.detect()

		assert result is False
		assert driver.device_found is False
