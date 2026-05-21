using System.Threading.Channels;

namespace ZScout.CompassSvc;

/// <summary>
/// Thread-safe cache for the latest heading data with Channel-based fan-out for SSE subscribers.
/// </summary>
public sealed class HeadingCache
{
	private readonly object _lock = new();
	private readonly List<Channel<HeadingData>> _subscribers = [];
	private HeadingData _latest = new();

	/// <summary>Get the latest cached heading data.</summary>
	public HeadingData Latest
	{
		get { lock (_lock) return _latest; }
	}

	/// <summary>Update the cached heading and broadcast to all SSE subscribers.</summary>
	public void Update(HeadingData data)
	{
		lock (_lock)
		{
			_latest = data;
		}

		// Broadcast to subscribers — remove any that are completed
		lock (_subscribers)
		{
			_subscribers.RemoveAll(ch =>
			{
				if (!ch.Writer.TryWrite(data))
				{
					ch.Writer.TryComplete();
					return true;
				}
				return false;
			});
		}
	}

	/// <summary>Subscribe to heading updates. Returns an async enumerable for SSE streaming.</summary>
	public ChannelReader<HeadingData> Subscribe()
	{
		var channel = Channel.CreateBounded<HeadingData>(new BoundedChannelOptions(16)
		{
			FullMode = BoundedChannelFullMode.DropOldest,
		});

		lock (_subscribers)
		{
			_subscribers.Add(channel);
		}

		return channel.Reader;
	}

	/// <summary>Unsubscribe a reader (best-effort cleanup).</summary>
	public void Unsubscribe(ChannelReader<HeadingData> reader)
	{
		lock (_subscribers)
		{
			_subscribers.RemoveAll(ch => ch.Reader == reader);
		}
	}
}
