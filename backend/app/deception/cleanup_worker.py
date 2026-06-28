import asyncio
import logging

logger = logging.getLogger("aegisnet.deception.cleanup")

CLEANUP_INTERVAL_SECONDS = 60


class CleanupWorker:
    def __init__(self, orchestrator):
        self._orchestrator = orchestrator

    async def run(self) -> None:
        logger.info("[cleanup] Decoy cleanup worker started.")
        while True:
            try:
                await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
                await self._sweep()
            except asyncio.CancelledError:
                logger.info("[cleanup] Cleanup worker cancelled.")
                return
            except Exception as exc:
                logger.error(f"[cleanup] Error during sweep: {exc}")

    async def _sweep(self) -> None:
        expired = await self._orchestrator.registry.get_expired()
        if not expired:
            return
        logger.info(f"[cleanup] Terminating {len(expired)} expired decoy(s)...")
        for record in expired:
            await self._orchestrator.terminate_decoy(record.decoy_id, reason="ttl_expired")
