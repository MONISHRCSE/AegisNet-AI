#!/usr/bin/env python3
"""
AegisNet AI — Database startup migration runner.
Run this script at container startup BEFORE launching uvicorn.
Executes: alembic upgrade head
"""
import asyncio
import subprocess
import sys
import time

import asyncpg

from app.core.config import settings
from app.core.logging import logger


async def wait_for_postgres(max_retries: int = 15, delay: float = 2.0) -> None:
    """Poll PostgreSQL until it is accepting connections."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = await asyncpg.connect(
                host=settings.POSTGRES_SERVER,
                port=int(settings.POSTGRES_PORT),
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
            )
            await conn.close()
            logger.info(f"[migrate] PostgreSQL ready after {attempt} attempt(s).")
            return
        except Exception as exc:
            logger.warning(f"[migrate] Attempt {attempt}/{max_retries} — DB not ready: {exc}")
            await asyncio.sleep(delay)
    logger.error("[migrate] PostgreSQL did not become ready in time. Aborting.")
    sys.exit(1)


def run_alembic_upgrade() -> None:
    """Run `alembic upgrade head` as a subprocess."""
    logger.info("[migrate] Running: alembic upgrade head")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=False,
    )
    if result.returncode != 0:
        logger.error("[migrate] Alembic migration failed.")
        sys.exit(result.returncode)
    logger.info("[migrate] Schema migration complete.")


if __name__ == "__main__":
    asyncio.run(wait_for_postgres())
    run_alembic_upgrade()
