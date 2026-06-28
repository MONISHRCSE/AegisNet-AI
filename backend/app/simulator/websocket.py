import json
import logging
from redis.asyncio import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class SimulatorWebsocket:
    """Handles broadcasting simulation events over Redis pubsub/streams."""
    
    @staticmethod
    async def broadcast_event(event_type: str, data: dict):
        try:
            redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
            msg = {"type": event_type, "data": data}
            
            # Use pubsub channel 'simulation_events'
            await redis.publish("channel:simulation_events", json.dumps(msg))
            logger.info(f"[Simulator WS] Broadcasted {event_type}")
            await redis.close()
        except Exception as e:
            logger.error(f"[Simulator WS] Broadcast failed: {e}")
