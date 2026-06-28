#!/usr/bin/env python3
"""
Standalone entrypoint to run the telemetry ingestion worker.
Designed to be started as a separate container or process.

Usage:
    python -m app.telemetry.run_worker

Environment Variables:
    ZEEK_LOG_PATH  — path to Zeek conn.log (default: /var/log/zeek/current/conn.log)
    REDIS_URL      — Redis connection URL
    MONGODB_URL    — MongoDB connection URL
    MONGODB_DB     — MongoDB database name
"""
import asyncio
import logging
import signal

from app.telemetry.worker import run_ingestion_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s",
)

logger = logging.getLogger("aegisnet.telemetry")


def handle_shutdown(loop: asyncio.AbstractEventLoop, task: asyncio.Task) -> None:
    logger.info("[run_worker] SIGTERM received — requesting graceful shutdown.")
    task.cancel()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    main_task = loop.create_task(run_ingestion_pipeline())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown, loop, main_task)

    try:
        loop.run_until_complete(main_task)
    except asyncio.CancelledError:
        logger.info("[run_worker] Pipeline cancelled. Exiting.")
    finally:
        loop.close()
