from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Any, List, Optional

from app.api.deps import get_current_user, get_current_active_admin
from app.db.mongodb import db as mongo

router = APIRouter()


@router.get("/alerts", response_model=List[Any])
async def list_alerts(
    alert_status: Optional[str] = Query(default=None, description="Filter: new | investigating | resolved"),
    category: Optional[str]     = Query(default=None, description="Filter by ML category"),
    min_severity: Optional[float] = Query(default=None, ge=0.0, le=10.0),
    limit: int = Query(default=50, le=200),
    skip: int  = Query(default=0,  ge=0),
    _: dict = Depends(get_current_user),
):
    query: dict = {}
    if alert_status:
        query["status"] = alert_status
    if category:
        query["ml_classification.category"] = category
    if min_severity is not None:
        query["severity_score"] = {"$gte": min_severity}

    cursor = (
        mongo.db["security_alerts"]
        .find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(limit)
    )
    results = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results


@router.get("/alerts/{alert_id}", response_model=Any)
async def get_alert(
    alert_id: str,
    _: dict = Depends(get_current_user),
):
    doc = await mongo.db["security_alerts"].find_one({"_alert_id": alert_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    doc["_id"] = str(doc["_id"])
    return doc


@router.patch("/alerts/{alert_id}/status", response_model=Any)
async def update_alert_status(
    alert_id: str,
    new_status: str = Query(..., description="new | investigating | resolved"),
    _: dict = Depends(get_current_user),
):
    valid_statuses = {"new", "investigating", "resolved"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )
    result = await mongo.db["security_alerts"].find_one_and_update(
        {"_alert_id": alert_id},
        {"$set": {"status": new_status}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    result["_id"] = str(result["_id"])
    return result


@router.get("/summary", response_model=Any)
async def alerts_summary(_: dict = Depends(get_current_user)):
    """Returns aggregate counts per severity band and category for dashboard widgets."""
    pipeline = [
        {
            "$group": {
                "_id": "$ml_classification.category",
                "count": {"$sum": 1},
                "avg_severity": {"$avg": "$severity_score"},
                "max_severity": {"$max": "$severity_score"},
            }
        },
        {"$sort": {"count": -1}},
    ]
    results = []
    async for doc in mongo.db["security_alerts"].aggregate(pipeline):
        results.append(doc)
    return {"breakdown": results}
