import redis.asyncio as redis
from app.core.config import settings

class RedisCache:
    client: redis.Redis = None

redis_cache = RedisCache()

async def connect_to_redis():
    redis_cache.client = await redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis_connection():
    await redis_cache.client.close()
