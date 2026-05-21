using Moq;
using Xunit;
using ZScout.CompassSvc;

namespace ZScout.CompassSvc.Tests;

public class CalculateHeadingTests
{
	[Fact]
	public void East_0_Degrees()
	{
		var heading = CompassService.CalculateHeading(100, 0);
		Assert.Equal(0.0, heading, precision: 1);
	}

	[Fact]
	public void North_90_Degrees()
	{
		var heading = CompassService.CalculateHeading(0, 100);
		Assert.Equal(90.0, heading, precision: 1);
	}

	[Fact]
	public void West_180_Degrees()
	{
		var heading = CompassService.CalculateHeading(-100, 0);
		Assert.Equal(180.0, heading, precision: 1);
	}

	[Fact]
	public void South_270_Degrees()
	{
		var heading = CompassService.CalculateHeading(0, -100);
		Assert.Equal(270.0, heading, precision: 1);
	}

	[Fact]
	public void Northeast_45_Degrees()
	{
		var heading = CompassService.CalculateHeading(100, 100);
		Assert.Equal(45.0, heading, precision: 1);
	}

	[Fact]
	public void Negative_Heading_Normalized()
	{
		var heading = CompassService.CalculateHeading(-100, -100);
		Assert.Equal(225.0, heading, precision: 1);
	}

	[Fact]
	public void All_Headings_In_Range()
	{
		for (int angle = 0; angle < 360; angle += 15)
		{
			double rad = angle * Math.PI / 180.0;
			short x = (short)(1000 * Math.Cos(rad));
			short y = (short)(1000 * Math.Sin(rad));
			var heading = CompassService.CalculateHeading(x, y);
			Assert.InRange(heading, 0.0, 360.0);
		}
	}
}

public class ConvertTemperatureTests
{
	[Fact]
	public void Positive_Temperature()
	{
		Assert.Equal(25.0, CompassService.ConvertTemperature(2500), precision: 1);
	}

	[Fact]
	public void Zero_Temperature()
	{
		Assert.Equal(0.0, CompassService.ConvertTemperature(0), precision: 1);
	}

	[Fact]
	public void Negative_Temperature()
	{
		Assert.Equal(-10.0, CompassService.ConvertTemperature(-1000), precision: 1);
	}
}

public class DetermineStatusTests
{
	[Fact]
	public void Healthy()
	{
		var reading = new RawReading(100, 200, 300, Qmc5883lDriver.StatusDrdy, 2500);
		Assert.Equal("healthy", CompassService.DetermineStatus(reading, deviceFound: true));
	}

	[Fact]
	public void Unavailable_When_Device_Not_Found()
	{
		var reading = new RawReading(100, 200, 300, Qmc5883lDriver.StatusDrdy, 2500);
		Assert.Equal("unavailable", CompassService.DetermineStatus(reading, deviceFound: false));
	}

	[Fact]
	public void Degraded_All_Zeros()
	{
		var reading = new RawReading(0, 0, 0, Qmc5883lDriver.StatusDrdy, 0);
		Assert.Equal("degraded", CompassService.DetermineStatus(reading, deviceFound: true));
	}

	[Fact]
	public void Degraded_Overflow()
	{
		var reading = new RawReading(100, 200, 300, Qmc5883lDriver.StatusOvl, 2500);
		Assert.Equal("degraded", CompassService.DetermineStatus(reading, deviceFound: true));
	}

	[Fact]
	public void Healthy_With_Data_Overrun()
	{
		var reading = new RawReading(100, 200, 300, (byte)(Qmc5883lDriver.StatusDrdy | Qmc5883lDriver.StatusDor), 2500);
		Assert.Equal("healthy", CompassService.DetermineStatus(reading, deviceFound: true));
	}
}

public class CompassServiceReadTests
{
	private static Mock<IQmc5883lDriver> CreateMockDriver(
		short x = 100, short y = 200, short z = 300,
		byte status = Qmc5883lDriver.StatusDrdy, short temp = 2500,
		bool deviceFound = true)
	{
		var mock = new Mock<IQmc5883lDriver>();
		mock.Setup(d => d.DeviceFound).Returns(deviceFound);
		mock.Setup(d => d.BusNumber).Returns(1);
		mock.Setup(d => d.Address).Returns(0x0d);
		mock.Setup(d => d.Read()).Returns(new RawReading(x, y, z, status, temp));
		return mock;
	}

	[Fact]
	public void ReadHeading_Returns_Valid_Data()
	{
		var mock = CreateMockDriver();
		var compass = new CompassService(mock.Object);
		var data = compass.ReadHeading();

		Assert.Equal(100, data.X);
		Assert.Equal(200, data.Y);
		Assert.Equal(300, data.Z);
		Assert.Equal("healthy", data.Status);
		Assert.Equal(CompassService.CalculateHeading(100, 200), data.HeadingDegrees, precision: 1);
		Assert.NotEmpty(data.Timestamp);
	}

	[Fact]
	public void ReadHeading_Unavailable_Returns_Zero_Heading()
	{
		var mock = CreateMockDriver(deviceFound: false);
		var compass = new CompassService(mock.Object);
		var data = compass.ReadHeading();

		Assert.Equal(0.0, data.HeadingDegrees);
		Assert.Equal("unavailable", data.Status);
	}

	[Fact]
	public void ReadRawAxes_Returns_Values()
	{
		var mock = CreateMockDriver();
		var compass = new CompassService(mock.Object);
		var (x, y, z, statusReg) = compass.ReadRawAxes();

		Assert.Equal(100, x);
		Assert.Equal(200, y);
		Assert.Equal(300, z);
		Assert.Equal(Qmc5883lDriver.StatusDrdy, statusReg);
	}

	[Fact]
	public void GetStatus_Returns_Healthy()
	{
		var mock = CreateMockDriver();
		var compass = new CompassService(mock.Object);
		var statusObj = compass.GetStatus();

		// Use reflection to check anonymous object properties
		var type = statusObj.GetType();
		Assert.Equal("healthy", type.GetProperty("status")!.GetValue(statusObj));
		Assert.Equal("0x0d", type.GetProperty("deviceAddress")!.GetValue(statusObj));
		Assert.Equal(1, type.GetProperty("i2cBus")!.GetValue(statusObj));
		Assert.Equal(true, type.GetProperty("deviceFound")!.GetValue(statusObj));
	}

	[Fact]
	public void GetStatus_Unavailable()
	{
		var mock = CreateMockDriver(deviceFound: false);
		var compass = new CompassService(mock.Object);
		var statusObj = compass.GetStatus();

		var type = statusObj.GetType();
		Assert.Equal("unavailable", type.GetProperty("status")!.GetValue(statusObj));
		Assert.Equal(false, type.GetProperty("deviceFound")!.GetValue(statusObj));
	}
}
