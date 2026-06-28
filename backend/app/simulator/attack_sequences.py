import asyncio
import json
import logging
from redis.asyncio import Redis
from app.core.config import settings
from app.simulator.attack_profiles import AttackProfiles

logger = logging.getLogger(__name__)

class AttackSequenceRunner:
    """Executes multi-stage attack scenarios over time."""
    
    def __init__(self):
        self.redis: Redis = Redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True
        )

    async def emit_flows(self, flows: list):
        """Sends Zeek flows into the Redis telemetry stream."""
        for flow in flows:
            # Drop the internal simulation flag before sending to ML
            is_malicious = flow.pop('_simulated_malicious', False)
            
            await self.redis.xadd(
                "stream:telemetry:raw_flows",
                flow
            )
            # Add small jitter between packets
            await asyncio.sleep(0.01)

    async def run_scenario_1_external_breach(self, attacker_ip: str, target_ip: str, honeypot_ip: str):
        """
        Scenario 1: Full kill chain
        1. Recon -> 2. Brute Force -> 3. Web Exploit -> 4. Lateral Movement to Honeypot
        """
        logger.info(f"[Simulator] Starting Scenario 1 from {attacker_ip} against {target_ip}")
        
        # 1. Reconnaissance
        logger.info(f"[{attacker_ip}] Stage 1: Port Scanning")
        flows = AttackProfiles.port_scan(attacker_ip, target_ip)
        await self.emit_flows(flows)
        await asyncio.sleep(2.0)
        
        # 2. Credential Access
        logger.info(f"[{attacker_ip}] Stage 2: SSH Brute Force")
        flows = AttackProfiles.ssh_brute_force(attacker_ip, target_ip)
        await self.emit_flows(flows)
        await asyncio.sleep(3.0)
        
        # 3. Web Exploitation
        logger.info(f"[{attacker_ip}] Stage 3: Web Exploitation")
        flows = AttackProfiles.web_exploit(attacker_ip, target_ip)
        await self.emit_flows(flows)
        await asyncio.sleep(5.0)
        
        # 4. Lateral Movement -> Honeypot
        logger.info(f"[{attacker_ip}] Stage 4: Lateral Movement to Honeypot")
        flows = AttackProfiles.lateral_movement(attacker_ip, honeypot_ip)
        await self.emit_flows(flows)
        await asyncio.sleep(2.0)
        
        logger.info(f"[{attacker_ip}] Stage 5: Honeypot Interaction")
        flows = AttackProfiles.honeypot_interaction(attacker_ip, honeypot_ip)
        await self.emit_flows(flows)
        
        logger.info(f"[Simulator] Scenario 1 completed for {attacker_ip}")

    async def close(self):
        await self.redis.close()
