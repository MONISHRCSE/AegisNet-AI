import asyncio
import logging
import random
from app.simulator.attack_sequences import AttackSequenceRunner
from app.simulator.traffic_generator import EXTERNAL_IPS
from app.simulator.attack_profiles import AttackProfiles

logger = logging.getLogger(__name__)

class SimulationScheduler:
    """Schedules background traffic and injects attacks at intervals."""
    
    def __init__(self):
        self.runner = AttackSequenceRunner()
        self.running = False

    async def _background_traffic_loop(self):
        while self.running:
            try:
                flows = AttackProfiles.generate_background_traffic(count=20)
                await self.runner.emit_flows(flows)
                await asyncio.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                logger.error(f"[Simulator] Background loop error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        self.running = True
        logger.info("[Simulator] Starting background traffic loop...")
        asyncio.create_task(self._background_traffic_loop())

    async def stop(self):
        self.running = False
        await self.runner.close()
        logger.info("[Simulator] Scheduler stopped.")

    async def inject_scenario_1(self, target_ip: str, honeypot_ip: str) -> str:
        """Injects a full attack scenario."""
        attacker = random.choice(EXTERNAL_IPS)
        logger.info(f"[Simulator] Injecting Scenario 1 from {attacker}")
        await self.runner.run_scenario_1_external_breach(attacker, target_ip, honeypot_ip)
        return attacker
