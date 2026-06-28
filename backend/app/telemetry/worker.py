import asyncio
import logging
import os

import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

from app.telemetry.parser import parse_conn_log_line
from app.telemetry.tailer import tail_file
from app.telemetry.producer import RedisStreamProducer
from app.telemetry.persister import MongoPersister

logger = logging.getLogger("aegisnet.telemetry.worker")

ZEEK_LOG_PATH = os.getenv("ZEEK_LOG_PATH", "/var/log/zeek/current/conn.log")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "aegisnet_logs")


async def run_ingestion_pipeline() -> None:
    """
    Main ingestion coroutine:
      1. Tail Zeek conn.log asynchronously
      2. Parse each line into a NetworkFlowEvent
      3. Publish to Redis Streams (for real-time ML inference)
      4. Persist to MongoDB (for forensic analysis & historical querying)
    """
    logger.info("[worker] Connecting to Redis and MongoDB...")

    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    from app.db.mongodb import _build_mongo_url
    safe_mongo_url = _build_mongo_url()
    mongo_client = AsyncIOMotorClient(safe_mongo_url)
    mongo_collection = mongo_client[MONGODB_DB]["network_flows"]

    producer = RedisStreamProducer(redis_client)
    persister = MongoPersister(mongo_collection)

    logger.info(f"[worker] Starting telemetry ingestion from: {ZEEK_LOG_PATH}")

    # Background periodic flush tasks
    flush_tasks = [
        asyncio.create_task(producer.periodic_flush()),
        asyncio.create_task(persister.periodic_flush()),
    ]

    parsed_count = 0
    skipped_count = 0

    try:
        async for line in tail_file(ZEEK_LOG_PATH):
            event = parse_conn_log_line(line)

            if event is None:
                skipped_count += 1
                continue

            # Dual-write: Redis stream + MongoDB persistence
            await asyncio.gather(
                producer.add(event),
                persister.add(event),
            )

            parsed_count += 1
            if parsed_count % 1000 == 0:
                logger.info(f"[worker] Ingested {parsed_count} flows | Skipped: {skipped_count}")

    except asyncio.CancelledError:
        logger.info("[worker] Shutdown signal received — flushing buffers...")
        await producer.flush()
        await persister.flush()

    finally:
        for task in flush_tasks:
            task.cancel()
        await redis_client.close()
        mongo_client.close()
        logger.info("[worker] Telemetry pipeline shut down cleanly.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s"
    )
    asyncio.run(run_ingestion_pipeline())
