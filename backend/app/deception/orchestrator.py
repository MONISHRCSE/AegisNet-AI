import asyncio
import logging
from typing import Optional

from app.deception.policy_engine import select_rule, DECOY_IMAGE_MAP, DECOY_INTERNAL_PORT_MAP
from app.deception.docker_manager import DockerManager
from app.deception.iptables_manager import IPTablesManager
from app.deception.decoy_registry import DecoyRegistry, DecoyRecord
from app.deception.interaction_logger import InteractionLogger

logger = logging.getLogger("aegisnet.deception.orchestrator")


class DeceptionOrchestrator:
    """
    Central orchestrator for the AegisNet adaptive deception engine.

    Workflow:
      alert received → policy_engine.select_rule() → DockerManager.deploy_decoy()
      → IPTablesManager.add_dnat_rule() → DecoyRegistry.register()
    """

    def __init__(self, mongo_db):
        self.docker   = DockerManager()
        self.iptables = IPTablesManager()
        self.registry = DecoyRegistry()
        self.logger   = InteractionLogger(mongo_db["honeypot_logs"])

    async def handle_alert(self, alert: dict) -> Optional[str]:
        """
        Entry point called by the Redis alert consumer.
        Returns decoy_id if a decoy was deployed, else None.
        """
        attacker_ip = alert.get("attacker_ip", "")
        category    = alert.get("category", "")
        dest_port   = int(alert.get("dest_port", 0))

        if not attacker_ip or not category:
            return None

        # Skip if an active decoy already targets this attacker
        if await self.registry.has_active_decoy_for(attacker_ip):
            logger.debug(f"[orchestrator] Active decoy already exists for {attacker_ip}")
            return None

        rule = select_rule(category, dest_port)
        if not rule:
            logger.debug(f"[orchestrator] No deception rule matched: {category}:{dest_port}")
            return None

        image        = DECOY_IMAGE_MAP[rule.decoy_type]
        internal_port = DECOY_INTERNAL_PORT_MAP[rule.decoy_type]

        # Deploy container on isolated honeynet
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.docker.deploy_decoy(
                image=image,
                decoy_id=attacker_ip.replace(".", "-"),
                internal_port=internal_port,
            ),
        )

        if not result:
            logger.error(f"[orchestrator] Docker deploy failed for {attacker_ip}")
            return None

        # Build registry record
        record = DecoyRecord(
            attacker_ip=attacker_ip,
            decoy_type=rule.decoy_type,
            container_id=result["container_id"],
            container_ip=result["container_ip"],
            decoy_port=internal_port,
            target_port=dest_port or internal_port,
            lifetime_minutes=rule.auto_terminate_minutes,
        )
        await self.registry.register(record)

        # Install DNAT rule (best-effort — fails gracefully in dev)
        await self.iptables.add_dnat_rule(
            attacker_ip=attacker_ip,
            target_port=record.target_port,
            decoy_ip=record.container_ip,
            decoy_port=internal_port,
        )

        logger.info(
            f"[orchestrator] Decoy deployed: {rule.decoy_type} "
            f"for {attacker_ip} → {result['container_ip']}:{internal_port}"
        )
        return record.decoy_id

    async def terminate_decoy(self, decoy_id: str, reason: str = "manual") -> bool:
        record = await self.registry.deregister(decoy_id)
        if not record:
            logger.warning(f"[orchestrator] Decoy {decoy_id[:8]} not found in registry.")
            return False

        # Remove DNAT rule
        await self.iptables.remove_dnat_rule(
            attacker_ip=record.attacker_ip,
            target_port=record.target_port,
            decoy_ip=record.container_ip,
            decoy_port=record.decoy_port,
        )

        # Stop container
        stopped = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self.docker.stop_decoy(record.container_id)
        )

        logger.info(
            f"[orchestrator] Decoy {decoy_id[:8]} terminated. "
            f"Reason: {reason}. Container stopped: {stopped}"
        )
        return stopped
