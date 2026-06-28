from fastapi import APIRouter, Depends, Query
from typing import List, Any
from datetime import datetime

from app.api.deps import get_current_user
from app.db.mongodb import db as mongo
from app.schemas.telemetry import SecurityAlert, NetworkFlow

router = APIRouter()


@router.get("/alerts", response_model=List[Any])
async def get_alerts(
    status: str = Query(default=None, description="Filter by status: new, investigating, resolved"),
    limit: int = Query(default=50, le=200),
    _: dict = Depends(get_current_user)
):
    query = {}
    if status:
        query["status"] = status

    cursor = mongo.db["security_alerts"].find(query).sort("timestamp", -1).limit(limit)
    alerts = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        alerts.append(doc)
    return alerts


@router.get("/flows", response_model=List[Any])
async def get_flows(
    source_ip: str = Query(default=None),
    limit: int = Query(default=100, le=500),
    _: dict = Depends(get_current_user)
):
    query = {}
    if source_ip:
        query["meta.source_ip"] = source_ip

    cursor = mongo.db["network_flows"].find(query).sort("timestamp", -1).limit(limit)
    flows = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        flows.append(doc)
    return flows


@router.get("/honeypot-logs", response_model=List[Any])
async def get_honeypot_logs(
    attacker_ip: str = Query(default=None),
    limit: int = Query(default=50, le=200),
    _: dict = Depends(get_current_user)
):
    query = {}
    if attacker_ip:
        query["attacker_ip"] = attacker_ip

    cursor = mongo.db["honeypot_logs"].find(query).sort("timestamp", -1).limit(limit)
    logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)
    return logs
