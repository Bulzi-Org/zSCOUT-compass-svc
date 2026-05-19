FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        i2c-tools && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN python3 -m pip install --no-cache-dir --break-system-packages .

EXPOSE 5100

ENV I2C_BUS=1
ENV I2C_ADDRESS=0x0d
ENV HTTP_PORT=5100

CMD ["python3", "-m", "compass_svc"]
