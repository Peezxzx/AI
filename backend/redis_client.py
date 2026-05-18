"""
Redis Client for Atsawin AI Event System
Provides Redis connection and operations
"""

import redis.asyncio as redis
import logging
from typing import Optional

# Global Redis client instance
redis_client = None

async def get_redis_client(host: str = "localhost", port: int = 6379, db: int = 0) -> redis.Redis:
    """
    Get Redis client instance
    
    Args:
        host: Redis host
        port: Redis port
        db: Redis database number
        
    Returns:
        Redis client instance
    """
    global redis_client
    
    if redis_client is None:
        redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            encoding='utf-8'
        )
        
        # Test connection
        try:
            await redis_client.ping()
            logging.info(f"Connected to Redis at {host}:{port}")
        except Exception as e:
            logging.error(f"Failed to connect to Redis: {e}")
            raise
    
    return redis_client

async def close_redis_client():
    """Close Redis client connection"""
    global redis_client
    
    if redis_client:
        await redis_client.close()
        redis_client = None
        logging.info("Redis client closed")

async def redis_publish(channel: str, message: str) -> bool:
    """
    Publish message to Redis channel
    
    Args:
        channel: Channel name
        message: Message to publish
        
    Returns:
        bool: True if published successfully
    """
    try:
        client = await get_redis_client()
        await client.publish(channel, message)
        return True
    except Exception as e:
        logging.error(f"Failed to publish to Redis channel {channel}: {e}")
        return False

async def redis_subscribe(channel: str):
    """
    Subscribe to Redis channel
    
    Args:
        channel: Channel name
        
    Returns:
        PubSub instance
    """
    try:
        client = await get_redis_client()
        return client.pubsub()
    except Exception as e:
        logging.error(f"Failed to subscribe to Redis channel {channel}: {e}")
        raise