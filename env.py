import os
from dataclasses import dataclass


@dataclass
class ENV:
    verbose: bool = os.environ.get("EXCHANGE_API_VERBOSE", False)
    redis_enabled: bool = os.environ.get("EXCHANGE_API_REDIS_ENABLED", False)
    redis_host: str = os.environ.get("EXCHANGE_API_REDIS_HOST", "127.0.0.1")
    redis_port: str = os.environ.get("EXCHANGE_API_REDIS_PORT", "6379")
