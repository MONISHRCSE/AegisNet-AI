import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("aegisnet.deception.logger")


def _sha256_interaction(
    attacker_ip: str,
    decoy_id: str,
    session_id: str,
    timestamp: str,
    payload: str,
) -> str:
    raw = f"{attacker_ip}{decoy_id}{session_id}{timestamp}{payload}"
    return hashlib.sha256(raw.encode()).hexdigest()


class InteractionLogger:
    """
    Persists honeypot interaction events to MongoDB honeypot_logs collection
    with SHA-256 forensic hashing for tamper evidence.
    """

    def __init__(self, mongo_collection):
        self._collection = mongo_collection
        self._buffer: list = []
        self._lock = asyncio.Lock()
        self._flush_interval = 2.0

    async def log(
        self,
        attacker_ip: str,
        decoy_id: str,
        honeypot_type: str,
        interaction_type: str,
        payload: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> None:
        session_id = session_id or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc)
        ts_str = timestamp.isoformat()
        payload_str = str(payload)

        log_hash = _sha256_interaction(
            attacker_ip, decoy_id, session_id, ts_str, payload_str
        )

        doc = {
            "timestamp": timestamp,
            "decoy_id": decoy_id,
            "attacker_ip": attacker_ip,
            "honeypot_type": honeypot_type,
            "interaction_type": interaction_type,
            "payload": payload,
            "session_id": session_id,
            "log_hash": log_hash,
        }

        async with self._lock:
            self._buffer.append(doc)

        logger.info(
            f"[interaction] {interaction_type} from {attacker_ip} "
            f"on {honeypot_type} decoy ({decoy_id[:8]})"
        )

    async def flush(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer.copy()
            self._buffer.clear()

        try:
            await self._collection.insert_many(batch, ordered=False)
            logger.debug(f"[interaction] Flushed {len(batch)} interaction logs.")
        except Exception as exc:
            logger.error(f"[interaction] MongoDB flush failed: {exc}")
            async with self._lock:
                self._buffer = batch + self._buffer

    async def periodic_flush(self) -> None:
        while True:
            await asyncio.sleep(self._flush_interval)
            await self.flush()
