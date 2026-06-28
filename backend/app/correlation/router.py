import os
from urllib.parse import quote_plus
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

router = APIRouter()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB", "aegisnet_logs")

def _build_mongo_url() -> str:
    user     = os.getenv("MONGO_USER", "")
    password = os.getenv("MONGO_PASSWORD", "")
    if user and password:
        return f"mongodb://{user}:{quote_plus(password)}@aegis-mongodb:27017"
    return MONGODB_URL

def _get_db():
    client = AsyncIOMotorClient(_build_mongo_url())
    return client[MONGODB_DB]


class StatusUpdate(BaseModel):
    status: str


@router.get("/incidents")
async def list_incidents(limit: int = 50, skip: int = 0):
    db = _get_db()
    cursor = db["incidents"].find({}, {"_id": 0}).sort("last_updated", -1).skip(skip).limit(limit)
    incidents = await cursor.to_list(length=limit)
    return {"status": "success", "data": incidents}


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    db = _get_db()
    incident = await db["incidents"].find_one({"incident_id": incident_id}, {"_id": 0})
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"status": "success", "data": incident}


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, payload: StatusUpdate):
    db = _get_db()
    result = await db["incidents"].update_one(
        {"incident_id": incident_id},
        {"$set": {"status": payload.status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Incident not found or status already set")
    return {"status": "success", "message": f"Incident status updated to {payload.status}"}


@router.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    db = _get_db()
    incident = await db["incidents"].find_one({"incident_id": incident_id}, {"_id": 0})
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    alert_ids = incident.get("alert_ids", [])
    cursor = db["security_alerts"].find(
        {"_alert_id": {"$in": alert_ids}}, {"_id": 0}
    ).sort("timestamp", 1)
    alerts = await cursor.to_list(length=200)
    return {"status": "success", "data": alerts}


@router.get("/topology")
async def get_topology_snapshot():
    db = _get_db()
    snapshot = await db["topology_snapshots"].find_one({"snapshot_id": "live"}, {"_id": 0})
    if not snapshot:
        return {"status": "success", "data": {"nodes": [], "edges": []}}
    return {"status": "success", "data": snapshot.get("graph", {})}


@router.get("/topology/live")
async def get_topology_live():
    return await get_topology_snapshot()


@router.get("/decoys/active")
async def get_active_decoys():
    db = _get_db()
    cursor = db["decoys"].find({"status": "active"}, {"_id": 0})
    decoys = await cursor.to_list(length=100)
    return {"status": "success", "data": decoys}


@router.get("/forensics/replay/{incident_id}")
async def forensics_replay(incident_id: str):
    return await get_incident_timeline(incident_id)
