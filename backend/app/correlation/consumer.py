import asyncio
import logging
import json
import os
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus

from app.correlation.correlator import Correlator
from app.correlation.topology_service import TopologyService
from app.api.websockets.telemetry import manager as ws_manager

logger = logging.getLogger("aegisnet.correlation.consumer")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB", "aegisnet_logs")

def _build_mongo_url() -> str:
    user     = os.getenv("MONGO_USER", "")
    password = os.getenv("MONGO_PASSWORD", "")
    if user and password:
        return f"mongodb://{user}:{quote_plus(password)}@aegis-mongodb:27017"
    return MONGODB_URL

ALERT_STREAM = "stream:ml:alerts"
CONSUMER_GROUP = "correlation-workers"
CONSUMER_NAME = f"correlator-{os.getpid()}"
BATCH_SIZE = 50
BLOCK_MS = 2000

class CorrelationEngine:
    def __init__(self, ws_manager):
        self.correlator = Correlator()
        self.topology = TopologyService()
        self.ws_manager = ws_manager
        
        self.redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
        self.mongo_client = AsyncIOMotorClient(_build_mongo_url())
        self.db = self.mongo_client[MONGODB_DB]

    async def _ensure_group(self):
        try:
            await self.redis_client.xgroup_create(ALERT_STREAM, CONSUMER_GROUP, id="0", mkstream=True)
            logger.info(f"[correlator] Created consumer group '{CONSUMER_GROUP}'")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"[correlator] Failed to create group: {e}")

    async def run(self):
        logger.info("[correlator] Starting Correlation Engine...")
        await self._ensure_group()
        
        try:
            while True:
                response = await self.redis_client.xreadgroup(
                    groupname=CONSUMER_GROUP,
                    consumername=CONSUMER_NAME,
                    streams={ALERT_STREAM: ">"},
                    count=BATCH_SIZE,
                    block=BLOCK_MS,
                )
                
                if not response:
                    continue
                    
                for _stream, messages in response:
                    ack_ids = []
                    for msg_id, raw_alert in messages:
                        try:
                            # Parse JSON fields if they are stringified
                            if "mitre_attack" in raw_alert and isinstance(raw_alert["mitre_attack"], str):
                                raw_alert["mitre_attack"] = json.loads(raw_alert["mitre_attack"].replace("'", '"'))
                            
                            incident = self.correlator.process_alert(raw_alert)
                            if incident:
                                self.topology.process_incident(incident)
                                
                                # Persist Incident
                                await self.db["incidents"].update_one(
                                    {"incident_id": incident.incident_id},
                                    {"$set": incident.to_mongo_doc()},
                                    upsert=True
                                )
                                
                                # Broadcast Incident Update
                                await self.ws_manager.broadcast(json.dumps({
                                    "type": "INCIDENT_UPDATE",
                                    "data": incident.to_mongo_doc()
                                }, default=str))
                                
                            ack_ids.append(msg_id)
                        except Exception as e:
                            logger.error(f"[correlator] Error processing alert {msg_id}: {e}")
                    
                    if ack_ids:
                        await self.redis_client.xack(ALERT_STREAM, CONSUMER_GROUP, *ack_ids)
                        
                        # Persist topology snapshot
                        await self.db["topology_snapshots"].update_one(
                            {"snapshot_id": "live"},
                            {"$set": {"graph": self.topology.get_live_graph()}},
                            upsert=True
                        )
                        
                        # Broadcast Topology Update
                        await self.ws_manager.broadcast(json.dumps({
                            "type": "TOPOLOGY_UPDATE",
                            "data": self.topology.get_live_graph()
                        }))

        except asyncio.CancelledError:
            logger.info("[correlator] Shutting down...")
        finally:
            await self.redis_client.close()
            self.mongo_client.close()
