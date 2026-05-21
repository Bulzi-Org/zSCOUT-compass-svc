FROM debian:bookworm-slim AS build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates && \
    wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh && \
    chmod +x /tmp/dotnet-install.sh && \
    /tmp/dotnet-install.sh --channel 10.0 --install-dir /usr/share/dotnet && \
    ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet && \
    rm -rf /var/lib/apt/lists/* /tmp/dotnet-install.sh

WORKDIR /app
COPY . .
RUN dotnet publish -c Release -o /out src/ZScout.CompassSvc

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        ca-certificates && \
    wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh && \
    chmod +x /tmp/dotnet-install.sh && \
    /tmp/dotnet-install.sh --channel 10.0 --runtime aspnetcore --install-dir /usr/share/dotnet && \
    ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet && \
    rm -rf /var/lib/apt/lists/* /tmp/dotnet-install.sh

COPY --from=build /out /app

EXPOSE 5100

ENV I2C_BUS=1
ENV I2C_ADDRESS=0x0d
ENV HTTP_PORT=5100

ENTRYPOINT ["dotnet", "/app/ZScout.CompassSvc.dll"]
