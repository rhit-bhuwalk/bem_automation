from redis.asyncio import Redis
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

class RedisDatabase:
    client: Redis = None
    _test_data = {}
    
    @classmethod
    async def connect(cls):
        """Connect to Redis"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data = {}  
            else:
                cls.client = Redis.from_url(
                    os.getenv("REDIS_URL", "redis://localhost:6379"),
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_keepalive=True,
                    socket_timeout=1,
                    retry_on_timeout=True,
                    retry_on_error=[asyncio.TimeoutError],
                    max_connections=10
                )
            print("Connected to Redis")
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            raise e
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls.client and not os.getenv("ENVIRONMENT") == "test":
            await cls.client.aclose()
            print("Closed connection to Redis")
    
    @classmethod
    async def flushdb(cls):
        """Clear all data in Redis"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data = {}
            else:
                await cls.client.flushdb()
        except Exception as e:
            print(f"Error flushing Redis database: {e}")
            raise e
    
    @classmethod
    async def hset(cls, key: str, field: str, value: str):
        """Set hash field to value"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                if key not in cls._test_data:
                    cls._test_data[key] = {}
                cls._test_data[key][field] = value
            else:
                await cls.client.hset(key, field, value)
        except Exception as e:
            print(f"Error setting hash field in Redis: {e}")
            raise e
    
    @classmethod
    async def hgetall(cls, key: str):
        """Get all fields and values in a hash"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                return cls._test_data.get(key, {})
            else:
                return await cls.client.hgetall(key)
        except Exception as e:
            print(f"Error getting hash fields from Redis: {e}")
            raise e
    
    @classmethod
    async def delete(cls, key: str):
        """Delete a key"""
        try:
            if os.getenv("ENVIRONMENT") == "test":
                cls._test_data.pop(key, None)
            else:
                await cls.client.delete(key)
        except Exception as e:
            print(f"Error deleting key from Redis: {e}")
            raise e

redis_db = RedisDatabase()