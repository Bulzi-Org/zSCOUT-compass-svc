# Clarification Log: C# Migration (#8)

## Q1: Should the Python source files be deleted in this PR?
**Decision**: Yes. The issue says "rewrite" — replace Python entirely with C#.

## Q2: Which .NET I2C library to use?
**Decision**: `System.Device.Gpio` NuGet package per the issue.

## Q3: How to handle I2C mocking in C# tests?
**Decision**: Extract an `IQmc5883lDriver` interface. Unit tests inject a mock driver.

## Q4: SSE implementation approach in Minimal API?
**Decision**: Write SSE frames directly to the response stream with `text/event-stream` content type.

## Q5: Should AGENTS.md and README.md be updated?
**Decision**: Yes. Update to reflect C#/.NET tech stack.

## Q6: Solution file format?
**Decision**: Use `.slnx` as specified in the issue.

## Q7: HeadingCache and HeadingReaderService purpose?
**Decision**: `HeadingReaderService` is an `IHostedService` that polls I2C. `HeadingCache` holds latest reading + subscriber broadcast via `Channel<T>`.
