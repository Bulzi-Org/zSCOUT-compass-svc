using System.Net;
using System.Text.Json;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Moq;
using Xunit;
using ZScout.CompassSvc;

namespace ZScout.CompassSvc.Tests;

public class TestWebApplicationFactory : WebApplicationFactory<Program>
{
	private readonly Mock<IQmc5883lDriver> _mockDriver;

	public TestWebApplicationFactory()
	{
		_mockDriver = new Mock<IQmc5883lDriver>();
		_mockDriver.Setup(d => d.DeviceFound).Returns(true);
		_mockDriver.Setup(d => d.BusNumber).Returns(1);
		_mockDriver.Setup(d => d.Address).Returns(0x0d);
		_mockDriver.Setup(d => d.Open()).Returns(true);
		_mockDriver.Setup(d => d.Read()).Returns(
			new RawReading(100, 200, 300, Qmc5883lDriver.StatusDrdy, 2500));
	}

	protected override void ConfigureWebHost(IWebHostBuilder builder)
	{
		builder.ConfigureServices(services =>
		{
			// Remove the real I2C driver registration
			var driverDescriptor = services.FirstOrDefault(d => d.ServiceType == typeof(IQmc5883lDriver));
			if (driverDescriptor is not null)
				services.Remove(driverDescriptor);

			// Remove only HeadingReaderService, not all IHostedService registrations
			var hostedDescriptors = services
				.Where(d => d.ServiceType == typeof(IHostedService)
					&& d.ImplementationType == typeof(HeadingReaderService))
				.ToList();
			foreach (var d in hostedDescriptors)
				services.Remove(d);

			// Add mock driver
			services.AddSingleton(_mockDriver.Object);

			// Seed the HeadingCache with test data so SSE tests get valid readings
			var cacheDescriptor = services.FirstOrDefault(d => d.ServiceType == typeof(HeadingCache));
			if (cacheDescriptor is not null)
				services.Remove(cacheDescriptor);

			var seededCache = new HeadingCache();
			seededCache.Update(new HeadingData
			{
				HeadingDegrees = CompassService.CalculateHeading(100, 200),
				X = 100,
				Y = 200,
				Z = 300,
				Temperature = 25.0,
				Overflow = false,
				DataReady = true,
				Timestamp = DateTime.UtcNow.ToString("o"),
				Status = "healthy",
			});
			services.AddSingleton(seededCache);
		});
	}
}

public class EndpointTests : IClassFixture<TestWebApplicationFactory>
{
	private readonly HttpClient _client;

	public EndpointTests(TestWebApplicationFactory factory)
	{
		_client = factory.CreateClient();
	}

	[Fact]
	public async Task GetStatus_Returns_Healthy()
	{
		var response = await _client.GetAsync("/api/status");

		Assert.Equal(HttpStatusCode.OK, response.StatusCode);
		var json = await response.Content.ReadAsStringAsync();
		using var doc = JsonDocument.Parse(json);
		var root = doc.RootElement;

		Assert.Equal("healthy", root.GetProperty("status").GetString());
		Assert.Equal("0x0d", root.GetProperty("deviceAddress").GetString());
		Assert.Equal(1, root.GetProperty("i2cBus").GetInt32());
		Assert.True(root.GetProperty("deviceFound").GetBoolean());
		Assert.False(root.GetProperty("overflow").GetBoolean());
		Assert.True(root.TryGetProperty("timestamp", out _));
	}

	[Fact]
	public async Task GetHeading_Returns_Valid_Data()
	{
		var response = await _client.GetAsync("/api/heading");

		Assert.Equal(HttpStatusCode.OK, response.StatusCode);
		var json = await response.Content.ReadAsStringAsync();
		using var doc = JsonDocument.Parse(json);
		var root = doc.RootElement;

		var heading = root.GetProperty("headingDegrees").GetDouble();
		Assert.InRange(heading, 0.0, 360.0);
		Assert.Equal(100, root.GetProperty("x").GetInt32());
		Assert.Equal(200, root.GetProperty("y").GetInt32());
		Assert.Equal(300, root.GetProperty("z").GetInt32());
		Assert.True(root.TryGetProperty("temperature", out _));
		Assert.True(root.TryGetProperty("overflow", out _));
		Assert.NotEmpty(root.GetProperty("timestamp").GetString()!);
	}

	[Fact]
	public async Task GetAxes_Returns_Raw_Values()
	{
		var response = await _client.GetAsync("/api/axes");

		Assert.Equal(HttpStatusCode.OK, response.StatusCode);
		var json = await response.Content.ReadAsStringAsync();
		using var doc = JsonDocument.Parse(json);
		var root = doc.RootElement;

		Assert.Equal(100, root.GetProperty("x").GetInt32());
		Assert.Equal(200, root.GetProperty("y").GetInt32());
		Assert.Equal(300, root.GetProperty("z").GetInt32());
		Assert.Equal($"0x{Qmc5883lDriver.StatusDrdy:x2}", root.GetProperty("statusRegister").GetString());
		Assert.True(root.TryGetProperty("timestamp", out _));
	}

	[Fact]
	public async Task StreamHeadings_Returns_SSE_Events()
	{
		var request = new HttpRequestMessage(HttpMethod.Get, "/api/stream/headings?intervalMs=50");
		var response = await _client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead);

		Assert.Equal(HttpStatusCode.OK, response.StatusCode);
		Assert.Equal("text/event-stream", response.Content.Headers.ContentType?.MediaType);

		using var stream = await response.Content.ReadAsStreamAsync();
		using var reader = new StreamReader(stream);

		var events = new List<JsonDocument>();
		var linesRead = 0;

		using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(10));

		try
		{
			while (events.Count < 3 && linesRead < 200)
			{
				var line = await reader.ReadLineAsync(cts.Token);
				if (line is null) break;
				linesRead++;

				if (line.StartsWith("data:"))
				{
					var payload = line["data:".Length..].Trim();
					events.Add(JsonDocument.Parse(payload));
				}
			}
		}
		catch (OperationCanceledException)
		{
			// Timeout is acceptable — check what we have
		}

		Assert.True(events.Count >= 2, $"Expected at least 2 SSE events, got {events.Count}");

		foreach (var evt in events)
		{
			var root = evt.RootElement;
			Assert.InRange(root.GetProperty("headingDegrees").GetDouble(), 0.0, 360.0);
			Assert.Equal(100, root.GetProperty("x").GetInt32());
			Assert.Equal(200, root.GetProperty("y").GetInt32());
			Assert.Equal(300, root.GetProperty("z").GetInt32());
			Assert.True(root.TryGetProperty("temperature", out _));
			Assert.NotEmpty(root.GetProperty("timestamp").GetString()!);
			evt.Dispose();
		}
	}
}
