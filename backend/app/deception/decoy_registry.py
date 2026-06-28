import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

logger = logging.getLogger("aegisnet.deception.registry")


class DecoyRecord:
    __slots__ = (
        "decoy_id", "attacker_ip", "decoy_type",
        "container_id", "container_ip", "decoy_port",
        "target_port", "deployed_at", "expires_at",
    )

    def __init__(
        self,
        attacker_ip: str,
        decoy_type: str,
        container_id: str,
        container_ip: str,
        decoy_port: int,
        target_port: int,
        lifetime_minutes: int,
    ):
        self.decoy_id = str(uuid.uuid4())
        self.attacker_ip = attacker_ip
        self.decoy_type = decoy_type
        self.container_id = container_id
        self.container_ip = container_ip
        self.decoy_port = decoy_port
        self.target_port = target_port
        self.deployed_at = datetime.now(timezone.utc)
        self.expires_at = self.deployed_at + timedelta(minutes=lifetime_minutes)

    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> dict:
        return {
            "decoy_id": self.decoy_id,
            "attacker_ip": self.attacker_ip,
            "decoy_type": self.decoy_type,
            "container_id": self.container_id,
            "container_ip": self.container_ip,
            "decoy_port": self.decoy_port,
            "target_port": self.target_port,
            "deployed_at": self.deployed_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }


class DecoyRegistry:
    """
    In-memory registry of all active decoy deployments.
    Keyed by attacker_ip for fast O(1) duplicate detection.
    """

    def __init__(self):
        self._by_attacker: Dict[str, DecoyRecord] = {}
        self._by_id: Dict[str, DecoyRecord] = {}
        self._lock = asyncio.Lock()

    async def register(self, record: DecoyRecord) -> None:
        async with self._lock:
            self._by_attacker[record.attacker_ip] = record
            self._by_id[record.decoy_id] = record
        logger.info(
            f"[registry] Registered decoy {record.decoy_id[:8]} "
            f"for attacker {record.attacker_ip}"
        )

    async def get_by_attacker(self, attacker_ip: str) -> Optional[DecoyRecord]:
        async with self._lock:
            return self._by_attacker.get(attacker_ip)

    async def get_by_id(self, decoy_id: str) -> Optional[DecoyRecord]:
        async with self._lock:
            return self._by_id.get(decoy_id)

    async def deregister(self, decoy_id: str) -> Optional[DecoyRecord]:
        async with self._lock:
            record = self._by_id.pop(decoy_id, None)
            if record:
                self._by_attacker.pop(record.attacker_ip, None)
        return record

    async def get_expired(self) -> list:
        async with self._lock:
            return [r for r in self._by_id.values() if r.is_expired()]

    async def all(self) -> list:
        async with self._lock:
            return list(self._by_id.values())

    async def has_active_decoy_for(self, attacker_ip: str) -> bool:
        async with self._lock:
            record = self._by_attacker.get(attacker_ip)
            return record is not None and not record.is_expired()
