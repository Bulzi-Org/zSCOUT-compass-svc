FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build

WORKDIR /app
COPY . .
RUN dotnet publish -c Release -r linux-arm64 --self-contained false -o /out src/ZScout.CompassSvc

FROM mcr.microsoft.com/dotnet/aspnet:10.0

COPY --from=build /out /app

EXPOSE 5100

ENV I2C_BUS=1
ENV I2C_ADDRESS=0x0d
ENV HTTP_PORT=5100

ENTRYPOINT ["dotnet", "/app/ZScout.CompassSvc.dll"]
