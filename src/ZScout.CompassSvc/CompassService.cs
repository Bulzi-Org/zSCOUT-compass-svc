namespace ZScout.CompassSvc;

/// <summary>Processed heading data from the compass sensor.</summary>
public sealed record HeadingData
{
	public double HeadingDegrees { get; init; }
	public short X { get; init; }
	public short Y { get; init; }
	public short Z { get; init; }
	public double Temperature { get; init; }
	public bool Overflow { get; init; }
	public bool DataReady { get; init; }
	public bool DataOverrun { get; init; }
	public string Timestamp { get; init; } = "";
	public string Status { get; init; } = "unavailable";
}

/// <summary>High-level compass service wrapping the I2C driver.</summary>
public sealed class CompassService
{
	private readonly IQmc5883lDriver _driver;

	public CompassService(IQmc5883lDriver driver)
	{
		_driver = driver;
	}

	public IQmc5883lDriver Driver => _driver;

	public bool Initialize() => _driver.Open();

	public void Shutdown() => _driver.Close();

	/// <summary>Calculate heading in degrees (0–360) from raw X and Y axis values.</summary>
	public static double CalculateHeading(short x, short y)
	{
		double headingRad = Math.Atan2(y, x);
		double headingDeg = headingRad * (180.0 / Math.PI);
		if (headingDeg < 0)
			headingDeg += 360.0;
		return headingDeg;
	}

	/// <summary>Convert raw temperature register value to Celsius.</summary>
	public static double ConvertTemperature(short raw) => raw / 100.0;

	/// <summary>Determine sensor health status.</summary>
	public static string DetermineStatus(RawReading reading, bool deviceFound)
	{
		if (!deviceFound)
			return "unavailable";

		// All-zero detection
		if (reading.X == 0 && reading.Y == 0 && reading.Z == 0)
			return "degraded";

		// Overflow detection
		if ((reading.Status & Qmc5883lDriver.StatusOvl) != 0)
			return "degraded";

		return "healthy";
	}

	/// <summary>Read current heading data from the sensor.</summary>
	public HeadingData ReadHeading()
	{
		var reading = _driver.Read();
		var status = DetermineStatus(reading, _driver.DeviceFound);
		var timestamp = DateTime.UtcNow.ToString("o");

		double headingDeg = 0.0;
		if (status != "unavailable" && !(reading.X == 0 && reading.Y == 0))
			headingDeg = CalculateHeading(reading.X, reading.Y);

		return new HeadingData
		{
			HeadingDegrees = headingDeg,
			X = reading.X,
			Y = reading.Y,
			Z = reading.Z,
			Temperature = ConvertTemperature(reading.TemperatureRaw),
			Overflow = (reading.Status & Qmc5883lDriver.StatusOvl) != 0,
			DataReady = (reading.Status & Qmc5883lDriver.StatusDrdy) != 0,
			DataOverrun = (reading.Status & Qmc5883lDriver.StatusDor) != 0,
			Timestamp = timestamp,
			Status = status,
		};
	}

	/// <summary>Read raw axis values and status register.</summary>
	public (short X, short Y, short Z, byte StatusRegister) ReadRawAxes()
	{
		var reading = _driver.Read();
		return (reading.X, reading.Y, reading.Z, reading.Status);
	}

	/// <summary>Get device status information.</summary>
	public object GetStatus()
	{
		var reading = _driver.Read();
		var status = DetermineStatus(reading, _driver.DeviceFound);

		return new
		{
			status,
			deviceAddress = $"0x{_driver.Address:x2}",
			i2cBus = _driver.BusNumber,
			deviceFound = _driver.DeviceFound,
			overflow = (reading.Status & Qmc5883lDriver.StatusOvl) != 0,
			timestamp = DateTime.UtcNow.ToString("o"),
		};
	}
}
