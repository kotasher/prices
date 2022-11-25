import logging as log

import redis.asyncio as redis

from env import ENV

redis_connection = None
redis_connection_pool = None

if ENV.redis_enabled:
    log.debug("REDIS enabled")
    redis_connection_pool = redis.ConnectionPool(
        host=ENV.redis_host, port=ENV.redis_port, db=0
    )
    redis_connection = redis.Redis(connection_pool=redis_connection_pool)
    log.debug(f"REDIS connection {redis_connection}")
