import asyncio
import logging
from typing import List, Dict, Any
from app.db.mongodb import db
from app.simulator.websocket import SimulatorWebsocket

logger = logging.getLogger(__name__)

class ForensicReplayEngine:
    """Replays an incident timeline sequentially to visualize the attack chain."""
    
    @staticmethod
    async def run_replay(incident_id: str, speed_multiplier: float = 1.0):
        logger.info(f"[Replay] Starting forensic replay for incident {incident_id}")
        incident = await db.db.incidents.find_one({"incident_id": incident_id})
        
        if not incident:
            logger.error(f"[Replay] Incident {incident_id} not found.")
            return False
            
        await SimulatorWebsocket.broadcast_event(
            "FORENSIC_REPLAY_READY", 
            {"incident_id": incident_id, "attacker_ip": incident.get("attacker_ip")}
        )
        
        # Get raw alerts belonging to this incident
        alert_ids = incident.get("alert_ids", [])
        alerts = await db.db.alerts.find({"id": {"$in": alert_ids}}).sort("timestamp", 1).to_list(length=1000)
        
        if not alerts:
            logger.warning("[Replay] No raw alerts found for incident.")
            return False
            
        logger.info(f"[Replay] Found {len(alerts)} alerts. Replaying chronologically...")
        
        last_ts = alerts[0].get("timestamp", 0)
        
        for alert in alerts:
            current_ts = alert.get("timestamp", 0)
            delay = (current_ts - last_ts) * speed_multiplier
            
            # Bound delay to avoid huge gaps in replay
            delay = min(delay, 5.0) 
            if delay > 0:
                await asyncio.sleep(delay)
                
            await SimulatorWebsocket.broadcast_event("FORENSIC_REPLAY_EVENT", alert)
            last_ts = current_ts
            
        logger.info("[Replay] Forensic replay finished.")
        return True
