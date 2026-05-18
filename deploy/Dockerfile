FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        i2c-tools \
        gcc \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
COPY src/ ./src/

RUN python3 -m pip install --no-cache-dir --break-system-packages . && \
    python3 -m grpc_tools.protoc \
        -Isrc/proto \
        --python_out=src/compass_svc/generated \
        --grpc_python_out=src/compass_svc/generated \
        src/proto/compass.proto

# Clean up build dependencies
RUN apt-get purge -y gcc python3-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 5100

ENV I2C_BUS=1
ENV I2C_ADDRESS=0x0d
ENV GRPC_PORT=5100

CMD ["python3", "-m", "compass_svc"]
