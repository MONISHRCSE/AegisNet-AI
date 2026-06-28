import asyncio
import logging
import os

import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

from app.deception.orchestrator import DeceptionOrchestrator
from app.deception.cleanup_worker import CleanupWorker

logger = logging.getLogger("aegisnet.deception.consumer")

REDIS_URL      = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MONGODB_URL    = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB     = os.getenv("MONGODB_DB", "aegisnet_logs")
ALERT_STREAM   = "stream:ml:alerts"
CONSUMER_GROUP = "deception-orchestrator"
CONSUMER_NAME  = f"deception-{os.getpid()}"
BATCH_SIZE     = 10
BLOCK_MS       = 3000


async def _ensure_group(redis_client: aioredis.Redis) -> None:
    try:
        await redis_client.xgroup_create(ALERT_STREAM, CONSUMER_GROUP, id="$", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def run_deception_consumer() -> None:
    logger.info("[consumer] Deception consumer starting...")

    redis_client = await aioredis.from_url(REDIS_URL, decode_responses=True)
    mongo_client = AsyncIOMotorClient(MONGODB_URL)

    orchestrator = DeceptionOrchestrator(mongo_client[MONGODB_DB])
    cleanup      = CleanupWorker(orchestrator)

    await _ensure_group(redis_client)

    cleanup_task       = asyncio.create_task(cleanup.run())
    log_flush_task     = asyncio.create_task(orchestrator.logger.periodic_flush())

    logger.info(f"[consumer] Listening on '{ALERT_STREAM}' as '{CONSUMER_NAME}'...")

    try:
        while True:
            response = await redis_client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={ALERT_STREAM: ">"},
                count=BATCH_SIZE,
                block=BLOCK_MS,
            )
            if not response:
                continue

            ack_ids = []
            for _stream, messages in response:
                for msg_id, alert in messages:
                    ack_ids.append(msg_id)
                    await orchestrator.handle_alert(alert)

            if ack_ids:
                await redis_client.xack(ALERT_STREAM, CONSUMER_GROUP, *ack_ids)

    except asyncio.CancelledError:
        logger.info("[consumer] Shutdown received.")
    finally:
        cleanup_task.cancel()
        log_flush_task.cancel()
        await orchestrator.logger.flush()
        await redis_client.close()
        mongo_client.close()
        logger.info("[consumer] Deception consumer shut down.")


if __name__ == "__main__":
    import signal
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(run_deception_consumer())
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, task.cancel)
    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    finally:
        loop.close()
