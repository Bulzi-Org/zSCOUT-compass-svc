using System.Buffers.Binary;
using System.Device.I2c;

namespace ZScout.CompassSvc;

/// <summary>Raw sensor reading from QMC5883L.</summary>
public readonly record struct RawReading(short X, short Y, short Z, byte Status, short TemperatureRaw);

/// <summary>Abstraction over the QMC5883L magnetometer for testability.</summary>
public interface IQmc5883lDriver
{
	int BusNumber { get; }
	int Address { get; }
	bool DeviceFound { get; }
	bool Open();
	void Close();
	RawReading Read();
	bool Detect();
}

/// <summary>QMC5883L magnetometer I2C driver using System.Device.I2c.</summary>
public sealed class Qmc5883lDriver : IQmc5883lDriver, IDisposable
{
	// Register addresses
	private const byte RegXoutL = 0x00;
	private const byte RegCtrl1 = 0x09;
	private const byte RegCtrl2 = 0x0A;
	private const byte RegSetReset = 0x0B;

	// Status register flags
	public const byte StatusDrdy = 0x01;
	public const byte StatusOvl = 0x02;
	public const byte StatusDor = 0x04;

	// CTRL1: Continuous mode, 200Hz ODR, 8G range, 512 OSR
	private const byte Ctrl1Continuous200Hz8G512Osr = 0x1D;

	private readonly ILogger<Qmc5883lDriver> _logger;
	private I2cDevice? _device;
	private bool _deviceFound;

	public Qmc5883lDriver(int busNumber, int address, ILogger<Qmc5883lDriver> logger)
	{
		BusNumber = busNumber;
		Address = address;
		_logger = logger;
	}

	public int BusNumber { get; }
	public int Address { get; }
	public bool DeviceFound => _deviceFound;

	public bool Open()
	{
		try
		{
			var settings = new I2cConnectionSettings(BusNumber, Address);
			_device = I2cDevice.Create(settings);

			// Reset the chip
			_device.Write([RegCtrl2, 0x80]);
			// Recommended SET/RESET period
			_device.Write([RegSetReset, 0x01]);
			// Configure: continuous mode, 200Hz, 8G range, 512 OSR
			_device.Write([RegCtrl1, Ctrl1Continuous200Hz8G512Osr]);

			_deviceFound = true;
			_logger.LogInformation(
				"QMC5883L initialized on bus {Bus} at address 0x{Address:x2}",
				BusNumber, Address);
			return true;
		}
		catch (Exception ex)
		{
			_logger.LogError(ex, "Failed to initialize QMC5883L");
			_deviceFound = false;
			return false;
		}
	}

	public void Close()
	{
		try
		{
			_device?.Dispose();
		}
		catch (Exception ex)
		{
			_logger.LogError(ex, "Error closing I2C device");
		}
		_device = null;
	}

	public RawReading Read()
	{
		if (_device is null || !_deviceFound)
			return default;

		try
		{
			// Write the register address, then read 9 bytes
			Span<byte> buf = stackalloc byte[9];
			_device.WriteRead([RegXoutL], buf);

			short x = BinaryPrimitives.ReadInt16LittleEndian(buf[0..2]);
			short y = BinaryPrimitives.ReadInt16LittleEndian(buf[2..4]);
			short z = BinaryPrimitives.ReadInt16LittleEndian(buf[4..6]);
			byte status = buf[6];
			short tempRaw = BinaryPrimitives.ReadInt16LittleEndian(buf[7..9]);

			return new RawReading(x, y, z, status, tempRaw);
		}
		catch (Exception ex)
		{
			_logger.LogError(ex, "Error reading QMC5883L");
			_deviceFound = false;
			return default;
		}
	}

	public bool Detect()
	{
		try
		{
			var settings = new I2cConnectionSettings(BusNumber, Address);
			using var device = I2cDevice.Create(settings);
			Span<byte> buf = stackalloc byte[1];
			device.WriteRead([0x06], buf); // Read status register
			_deviceFound = true;
			return true;
		}
		catch
		{
			_deviceFound = false;
			return false;
		}
	}

	public void Dispose() => Close();
}
