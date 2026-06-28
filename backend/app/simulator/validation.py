import asyncio
import logging
from typing import Dict, Any
from app.db.mongodb import db

logger = logging.getLogger(__name__)

class SimulatorValidator:
    """Validates that attacks correctly trigger the pipeline."""

    @staticmethod
    async def validate_incident_creation(attacker_ip: str) -> bool:
        """Checks if an incident was created for the simulated attacker."""
        incident = await db.db.incidents.find_one({"attacker_ip": attacker_ip})
        if incident:
            logger.info(f"[Validation] SUCCESS: Incident found for {attacker_ip}. Severity: {incident.get('severity')}")
            return True
        logger.error(f"[Validation] FAILED: No incident generated for {attacker_ip}")
        return False

    @staticmethod
    async def validate_topology_updates(attacker_ip: str) -> bool:
        """Checks if the attacker appears in the topology graph."""
        snapshot = await db.db.topology_snapshots.find_one({"snapshot_id": "live"})
        if snapshot and "graph" in snapshot:
            nodes = snapshot["graph"].get("nodes", [])
            for node in nodes:
                if node.get("id") == attacker_ip:
                    logger.info(f"[Validation] SUCCESS: Topology node found for {attacker_ip}")
                    return True
        logger.error(f"[Validation] FAILED: Attacker {attacker_ip} missing from topology")
        return False

    @staticmethod
    async def validate_mitre_progression(attacker_ip: str, expected_tactics: list) -> bool:
        """Checks if the incident correctly mapped to expected MITRE tactics."""
        incident = await db.db.incidents.find_one({"attacker_ip": attacker_ip})
        if not incident:
            return False
            
        tactics_found = [m['tactic'] for m in incident.get('mitre_tactics', [])]
        missing = [t for t in expected_tactics if t not in tactics_found]
        
        if not missing:
            logger.info(f"[Validation] SUCCESS: MITRE progression validated for {attacker_ip}")
            return True
        logger.error(f"[Validation] FAILED: Missing MITRE tactics {missing} for {attacker_ip}")
        return False
        
    @staticmethod
    async def run_full_validation(attacker_ip: str):
        logger.info("=== Running End-to-End Validation ===")
        # Wait for correlation engine to process stream
        await asyncio.sleep(5.0) 
        
        i_ok = await SimulatorValidator.validate_incident_creation(attacker_ip)
        t_ok = await SimulatorValidator.validate_topology_updates(attacker_ip)
        m_ok = await SimulatorValidator.validate_mitre_progression(
            attacker_ip, 
            ["Discovery", "Credential Access", "Initial Access", "Lateral Movement"]
        )
        
        if i_ok and t_ok and m_ok:
            logger.info("=== Validation PASSED ===")
            return True
        else:
            logger.error("=== Validation FAILED ===")
            return False
