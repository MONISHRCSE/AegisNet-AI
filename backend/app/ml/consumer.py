import asyncio
import logging
import os
from typing import List

import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

from app.ml.inference import run_inference
from app.ml.loader import ModelRegistry

logger = logging.getLogger("aegisnet.ml.consumer")

REDIS_URL          = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MONGODB_URL        = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB         = os.getenv("MONGODB_DB", "aegisnet_logs")
CONSUMER_GROUP     = "ml-workers"
CONSUMER_NAME      = f"ml-consumer-{os.getpid()}"
INGEST_STREAM      = "stream:telemetry:raw_flows"
ALERT_STREAM       = "stream:ml:alerts"
BATCH_SIZE         = 50           # Events read per XREADGROUP call
BLOCK_MS           = 2000         # Block for 2s waiting for new messages
ALERT_STREAM_MAXLEN = 50_000


async def _ensure_consumer_group(redis_client: aioredis.Redis) -> None:
    """Create the consumer group if it doesn't exist (idempotent)."""
    try:
        await redis_client.xgroup_create(
            INGEST_STREAM, CONSUMER_GROUP, id="0", mkstream=True
        )
        logger.info(f"[consumer] Created consumer group '{CONSUMER_GROUP}'")
    except Exception as exc:
        if "BUSYGROUP" in str(exc):
            logger.debug(f"[consumer] Consumer group '{CONSUMER_GROUP}' already exists.")
        else:
            raise


async def _process_batch(
    messages: list,
    redis_client: aioredis.Redis,
    mongo_collection,
) -> None:
    alert_docs = []
    alert_records = []
    ack_ids = []

    for message_id, raw in messages:
        ack_ids.append(message_id)
        alert = run_inference(raw)
        if alert is None:
            continue
        alert_docs.append(alert.to_mongo_doc())
        alert_records.append((message_id, alert.to_redis_record()))

    # ── Persist alerts to MongoDB ────────────────────────────────────────
    if alert_docs:
        try:
            await mongo_collection.insert_many(alert_docs, ordered=False)
            logger.info(f"[consumer] Persisted {len(alert_docs)} alerts to MongoDB.")
        except Exception as exc:
            logger.error(f"[consumer] MongoDB alert insert failed: {exc}")

    # ── Publish alerts to Redis alert stream ─────────────────────────────
    if alert_records:
        pipeline = redis_client.pipeline(transaction=False)
        for _, record in alert_records:
            pipeline.xadd(ALERT_STREAM, record, maxlen=ALERT_STREAM_MAXLEN, approximate=True)
        try:
            await pipeline.execute()
            logger.info(f"[consumer] Published {len(alert_records)} alerts to {ALERT_STREAM}.")
        except Exception as exc:
            logger.error(f"[consumer] Redis alert stream publish failed: {exc}")

    # ── Acknowledge processed messages ───────────────────────────────────
    if ack_ids:
        await redis_client.xack(INGEST_STREAM, CONSUMER_GROUP, *ack_ids)


async def run_ml_consumer() -> None:
    """
    Main ML inference consumer loop.
    Reads from stream:telemetry:raw_flows via consumer group,
    runs inference, writes alerts to MongoDB + stream:ml:alerts.
    """
    logger.info("[consumer] Initialising ML inference consumer...")

    # Pre-load models at startup
    registry = ModelRegistry.get()
    if not registry.is_trained():
        logger.warning("[consumer] Models not trained yet — running in passthrough mode.")

    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    from app.db.mongodb import _build_mongo_url
    safe_mongo_url = _build_mongo_url()
    mongo_client = AsyncIOMotorClient(safe_mongo_url)
    mongo_collection = mongo_client[MONGODB_DB]["security_alerts"]

    await _ensure_consumer_group(redis_client)

    logger.info(f"[consumer] Listening on '{INGEST_STREAM}' as '{CONSUMER_NAME}'...")

    try:
        while True:
            response = await redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={INGEST_STREAM: ">"},
                count=BATCH_SIZE,
                block=BLOCK_MS,
            )

            if not response:
                continue

            for _stream_name, messages in response:
                await _process_batch(messages, redis_client, mongo_collection)

    except asyncio.CancelledError:
        logger.info("[consumer] Shutdown signal — flushing and closing connections.")
    finally:
        await redis_client.close()
        mongo_client.close()
        logger.info("[consumer] ML consumer shut down cleanly.")


if __name__ == "__main__":
    import signal
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(run_ml_consumer())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, main_task.cancel)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
