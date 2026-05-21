using System.Text.Json;
using System.Text.Json.Serialization;
using ZScout.CompassSvc;

var builder = WebApplication.CreateBuilder(args);

// Read configuration from environment variables
var i2cBus = int.Parse(Environment.GetEnvironmentVariable("I2C_BUS") ?? "1");
var i2cAddressStr = Environment.GetEnvironmentVariable("I2C_ADDRESS") ?? "0x0d";
var i2cAddress = i2cAddressStr.StartsWith("0x", StringComparison.OrdinalIgnoreCase)
	? Convert.ToInt32(i2cAddressStr, 16)
	: int.Parse(i2cAddressStr);
var httpPort = int.Parse(Environment.GetEnvironmentVariable("HTTP_PORT") ?? "5100");

// Configure JSON serialization for camelCase
builder.Services.ConfigureHttpJsonOptions(options =>
{
	options.SerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
	options.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.Never;
});

// Register services
builder.Services.AddSingleton<IQmc5883lDriver>(sp =>
	new Qmc5883lDriver(i2cBus, i2cAddress, sp.GetRequiredService<ILogger<Qmc5883lDriver>>()));
builder.Services.AddSingleton<CompassService>();
builder.Services.AddSingleton<HeadingCache>();
builder.Services.AddHostedService<HeadingReaderService>();

builder.WebHost.UseUrls($"http://0.0.0.0:{httpPort}");

var app = builder.Build();

// GET /api/status
app.MapGet("/api/status", (CompassService compass) => compass.GetStatus());

// GET /api/heading
app.MapGet("/api/heading", (CompassService compass) =>
{
	var data = compass.ReadHeading();
	return new
	{
		headingDegrees = data.HeadingDegrees,
		x = (int)data.X,
		y = (int)data.Y,
		z = (int)data.Z,
		temperature = data.Temperature,
		overflow = data.Overflow,
		timestamp = data.Timestamp,
	};
});

// GET /api/axes
app.MapGet("/api/axes", (CompassService compass) =>
{
	var (x, y, z, statusReg) = compass.ReadRawAxes();
	return new
	{
		x = (int)x,
		y = (int)y,
		z = (int)z,
		statusRegister = $"0x{statusReg:x2}",
		timestamp = DateTime.UtcNow.ToString("o"),
	};
});

// GET /api/stream/headings (SSE)
app.MapGet("/api/stream/headings", async (
	HttpContext context,
	HeadingCache cache,
	int intervalMs = 100) =>
{
	// Clamp interval
	intervalMs = Math.Clamp(intervalMs, 10, 10000);

	context.Response.ContentType = "text/event-stream";
	context.Response.Headers.CacheControl = "no-cache";
	context.Response.Headers.Connection = "keep-alive";

	var reader = cache.Subscribe();
	var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };

	try
	{
		while (!context.RequestAborted.IsCancellationRequested)
		{
			// Wait for next heading from cache or use interval-based polling
			HeadingData heading;
			using var cts = CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted);
			cts.CancelAfter(TimeSpan.FromMilliseconds(intervalMs * 2));

			try
			{
				if (await reader.WaitToReadAsync(cts.Token))
				{
					// Drain to latest
					while (reader.TryRead(out var item))
						heading = item;
					heading = cache.Latest;
				}
				else
				{
					heading = cache.Latest;
				}
			}
			catch (OperationCanceledException) when (!context.RequestAborted.IsCancellationRequested)
			{
				heading = cache.Latest;
			}

			var payload = JsonSerializer.Serialize(new
			{
				headingDegrees = heading.HeadingDegrees,
				x = (int)heading.X,
				y = (int)heading.Y,
				z = (int)heading.Z,
				temperature = heading.Temperature,
				timestamp = heading.Timestamp,
			}, jsonOptions);

			await context.Response.WriteAsync($"event: heading\ndata: {payload}\n\n", context.RequestAborted);
			await context.Response.Body.FlushAsync(context.RequestAborted);
			await Task.Delay(intervalMs, context.RequestAborted);
		}
	}
	catch (OperationCanceledException)
	{
		// Client disconnected
	}
	finally
	{
		cache.Unsubscribe(reader);
	}
});

app.Run();

// Make Program accessible for WebApplicationFactory in tests
public partial class Program { }
