namespace ZScout.CompassSvc;

/// <summary>
/// Background service that continuously polls the I2C driver and updates the heading cache.
/// </summary>
public sealed class HeadingReaderService : BackgroundService
{
	private readonly CompassService _compass;
	private readonly HeadingCache _cache;
	private readonly ILogger<HeadingReaderService> _logger;
	private readonly int _intervalMs;

	public HeadingReaderService(
		CompassService compass,
		HeadingCache cache,
		ILogger<HeadingReaderService> logger,
		IConfiguration configuration)
	{
		_compass = compass;
		_cache = cache;
		_logger = logger;
		_intervalMs = configuration.GetValue("STREAM_INTERVAL_MS", 100);
	}

	protected override async Task ExecuteAsync(CancellationToken stoppingToken)
	{
		_logger.LogInformation("HeadingReaderService starting — polling every {Interval}ms", _intervalMs);

		if (!_compass.Initialize())
		{
			_logger.LogWarning("Sensor not available — running in degraded mode");
		}

		using var timer = new PeriodicTimer(TimeSpan.FromMilliseconds(_intervalMs));

		try
		{
			while (await timer.WaitForNextTickAsync(stoppingToken))
			{
				var heading = _compass.ReadHeading();
				_cache.Update(heading);
			}
		}
		catch (OperationCanceledException)
		{
			_logger.LogInformation("HeadingReaderService stopping");
		}
		finally
		{
			_compass.Shutdown();
		}
	}
}
