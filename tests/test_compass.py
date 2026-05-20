"""Unit tests for compass service logic."""

import math
import pytest
from unittest.mock import MagicMock, patch

from compass_svc.compass import (
	calculate_heading,
	convert_temperature,
	determine_status,
	CompassService,
)
from compass_svc.i2c_driver import RawReading, STATUS_DRDY, STATUS_OVL, STATUS_DOR


class TestCalculateHeading:
	def test_east_0_degrees(self):
		"""Positive X, zero Y → 0° (East)."""
		heading = calculate_heading(100, 0)
		assert heading == pytest.approx(0.0, abs=0.1)

	def test_north_90_degrees(self):
		"""Zero X, positive Y → 90° (North)."""
		heading = calculate_heading(0, 100)
		assert heading == pytest.approx(90.0, abs=0.1)

	def test_west_180_degrees(self):
		"""Negative X, zero Y → 180° (West)."""
		heading = calculate_heading(-100, 0)
		assert heading == pytest.approx(180.0, abs=0.1)

	def test_south_270_degrees(self):
		"""Zero X, negative Y → 270° (South)."""
		heading = calculate_heading(0, -100)
		assert heading == pytest.approx(270.0, abs=0.1)

	def test_northeast_45_degrees(self):
		"""Equal positive X and Y → 45°."""
		heading = calculate_heading(100, 100)
		assert heading == pytest.approx(45.0, abs=0.1)

	def test_negative_heading_normalized(self):
		"""Negative angle should be normalized to 0-360 range."""
		heading = calculate_heading(-100, -100)
		assert heading == pytest.approx(225.0, abs=0.1)

	def test_all_headings_in_range(self):
		"""All headings should be in 0-360 range."""
		for angle_deg in range(0, 360, 15):
			angle_rad = math.radians(angle_deg)
			x = int(1000 * math.cos(angle_rad))
			y = int(1000 * math.sin(angle_rad))
			heading = calculate_heading(x, y)
			assert 0.0 <= heading < 360.0, f"Heading {heading} out of range for angle {angle_deg}"


class TestConvertTemperature:
	def test_positive_temperature(self):
		assert convert_temperature(2500) == pytest.approx(25.0)

	def test_zero_temperature(self):
		assert convert_temperature(0) == pytest.approx(0.0)

	def test_negative_temperature(self):
		assert convert_temperature(-1000) == pytest.approx(-10.0)


class TestDetermineStatus:
	def test_healthy(self):
		reading = RawReading(x=100, y=200, z=300, status=STATUS_DRDY)
		assert determine_status(reading, device_found=True) == "healthy"

	def test_unavailable_when_device_not_found(self):
		reading = RawReading(x=100, y=200, z=300, status=STATUS_DRDY)
		assert determine_status(reading, device_found=False) == "unavailable"

	def test_degraded_all_zeros(self):
		reading = RawReading(x=0, y=0, z=0, status=STATUS_DRDY)
		assert determine_status(reading, device_found=True) == "degraded"

	def test_degraded_overflow(self):
		reading = RawReading(x=100, y=200, z=300, status=STATUS_OVL)
		assert determine_status(reading, device_found=True) == "degraded"

	def test_healthy_with_data_overrun(self):
		"""DOR flag alone does not degrade status."""
		reading = RawReading(x=100, y=200, z=300, status=STATUS_DRDY | STATUS_DOR)
		assert determine_status(reading, device_found=True) == "healthy"


class TestCompassService:
	def test_read_heading(self, driver_with_mock_bus):
		compass = CompassService(driver_with_mock_bus)
		data = compass.read_heading()

		assert data.x_raw == 100
		assert data.y_raw == 200
		assert data.z_raw == 300
		assert data.status == "healthy"
		assert data.heading_degrees == pytest.approx(calculate_heading(100, 200), abs=0.1)
		assert data.timestamp_utc != ""

	def test_read_heading_unavailable(self):
		"""When device is not found, heading should be 0 and status unavailable."""
		from compass_svc.i2c_driver import QMC5883L
		driver = QMC5883L(bus_number=1, address=0x0d)
		compass = CompassService(driver)
		data = compass.read_heading()

		assert data.heading_degrees == 0.0
		assert data.status == "unavailable"

	def test_read_raw_axes(self, driver_with_mock_bus):
		compass = CompassService(driver_with_mock_bus)
		x, y, z, status = compass.read_raw_axes()

		assert x == 100
		assert y == 200
		assert z == 300
		assert status == STATUS_DRDY

	def test_get_status(self, driver_with_mock_bus):
		compass = CompassService(driver_with_mock_bus)
		status_info = compass.get_status()

		assert status_info["deviceFound"] is True
		assert status_info["i2cBus"] == "1"
		assert status_info["deviceAddress"] == "0x0d"
		assert status_info["status"] == "healthy"

	def test_get_status_unavailable(self):
		from compass_svc.i2c_driver import QMC5883L
		driver = QMC5883L(bus_number=1, address=0x0d)
		compass = CompassService(driver)
		status_info = compass.get_status()

		assert status_info["deviceFound"] is False
		assert status_info["status"] == "unavailable"
