import asyncio
import logging
from typing import List

import redis.asyncio as redis

from app.telemetry.models import NetworkFlowEvent

logger = logging.getLogger("aegisnet.telemetry.producer")

REDIS_STREAM_KEY = "stream:telemetry:raw_flows"
STREAM_MAXLEN = 100_000          # Cap stream at 100k entries (approx)
BATCH_SIZE = 50                  # Flush to Redis every N events
BATCH_TIMEOUT_SECONDS = 1.0      # Or every 1 second, whichever comes first


class RedisStreamProducer:
    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client
        self._buffer: List[NetworkFlowEvent] = []
        self._flush_lock = asyncio.Lock()

    async def add(self, event: NetworkFlowEvent) -> None:
        """Buffer an event. Flush when batch size is reached."""
        self._buffer.append(event)
        if len(self._buffer) >= BATCH_SIZE:
            await self.flush()

    async def flush(self) -> None:
        """Write all buffered events to Redis Streams atomically."""
        async with self._flush_lock:
            if not self._buffer:
                return

            batch = self._buffer.copy()
            self._buffer.clear()

        pipeline = self._redis.pipeline(transaction=False)
        for event in batch:
            pipeline.xadd(
                REDIS_STREAM_KEY,
                event.to_redis_record(),
                maxlen=STREAM_MAXLEN,
                approximate=True,
            )

        try:
            await pipeline.execute()
            logger.debug(f"[producer] Flushed {len(batch)} events to Redis stream.")
        except Exception as exc:
            logger.error(f"[producer] Redis pipeline flush failed: {exc}")
            # Re-buffer on failure for retry on next cycle
            async with self._flush_lock:
                self._buffer = batch + self._buffer

    async def periodic_flush(self) -> None:
        """Background task: flush on timeout even if batch is not full."""
        while True:
            await asyncio.sleep(BATCH_TIMEOUT_SECONDS)
            await self.flush()
