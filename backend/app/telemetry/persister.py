import asyncio
import logging
from typing import List

from motor.motor_asyncio import AsyncIOMotorCollection

from app.telemetry.models import NetworkFlowEvent

logger = logging.getLogger("aegisnet.telemetry.persister")

MONGO_COLLECTION = "network_flows"
BATCH_SIZE = 100
BATCH_TIMEOUT_SECONDS = 2.0


class MongoPersister:
    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection
        self._buffer: List[NetworkFlowEvent] = []
        self._flush_lock = asyncio.Lock()

    async def add(self, event: NetworkFlowEvent) -> None:
        self._buffer.append(event)
        if len(self._buffer) >= BATCH_SIZE:
            await self.flush()

    async def flush(self) -> None:
        async with self._flush_lock:
            if not self._buffer:
                return
            batch = self._buffer.copy()
            self._buffer.clear()

        documents = [event.to_mongo_doc() for event in batch]

        try:
            result = await self._collection.insert_many(documents, ordered=False)
            logger.debug(f"[persister] Inserted {len(result.inserted_ids)} flow docs into MongoDB.")
        except Exception as exc:
            logger.error(f"[persister] MongoDB batch insert failed: {exc}")
            # Re-buffer on failure
            async with self._flush_lock:
                self._buffer = batch + self._buffer

    async def periodic_flush(self) -> None:
        while True:
            await asyncio.sleep(BATCH_TIMEOUT_SECONDS)
            await self.flush()
