"""Configuration from environment variables."""

import os


I2C_BUS: int = int(os.environ.get("I2C_BUS", "1"))
I2C_ADDRESS: int = int(os.environ.get("I2C_ADDRESS", "0x0d"), 16) if os.environ.get("I2C_ADDRESS", "").startswith("0x") else int(os.environ.get("I2C_ADDRESS", "13"))
GRPC_PORT: int = int(os.environ.get("GRPC_PORT", "5100"))
STREAM_INTERVAL_MS: int = int(os.environ.get("STREAM_INTERVAL_MS", "100"))
