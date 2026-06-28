import asyncio
import logging
from app.simulator.scheduler import SimulationScheduler
from app.simulator.validation import SimulatorValidator
from app.simulator.metrics import SimulationMetrics
from app.db.mongodb import connect_to_mongo, close_mongo_connection

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main():
    logger.info("Initializing AegisNet AI Simulator...")
    await connect_to_mongo()
    
    scheduler = SimulationScheduler()
    metrics = SimulationMetrics()
    
    try:
        # 1. Start background traffic
        await scheduler.start()
        logger.info("Waiting 5 seconds to establish baseline background traffic...")
        await asyncio.sleep(5)
        
        # 2. Inject Scenario
        target = "10.0.0.55"      # Simulated internal web server
        honeypot = "10.0.0.100"   # Simulated internal honeypot
        
        attacker_ip = await scheduler.inject_scenario_1(target, honeypot)
        metrics.record_attack()
        
        # 3. Wait for correlation engine (running in docker) to process the stream
        logger.info("Attack complete. Waiting 10 seconds for ML and Correlation Engine to process streams...")
        await asyncio.sleep(10)
        
        # 4. Validate end-to-end functionality
        success = await SimulatorValidator.run_full_validation(attacker_ip)
        
        # 5. Export metrics
        await metrics.calculate_end_of_run_metrics()
        metrics.export()
        logger.info(f"Simulation completed. Validation {'PASSED' if success else 'FAILED'}.")
        
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user.")
    finally:
        await scheduler.stop()
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
