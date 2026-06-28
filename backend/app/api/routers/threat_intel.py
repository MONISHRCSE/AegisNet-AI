from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_current_user, get_current_active_admin
from app.db.postgres import get_db
from app.schemas.threat_intel import (
    ThreatIntelligenceCreate, ThreatIntelligenceResponse
)
from app.services import threat_intel_service

router = APIRouter()


@router.get("/", response_model=List[ThreatIntelligenceResponse])
async def list_indicators(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    return await threat_intel_service.get_all(db, skip=skip, limit=limit)


@router.post("/", response_model=ThreatIntelligenceResponse, status_code=status.HTTP_201_CREATED)
async def add_indicator(
    data: ThreatIntelligenceCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    existing = await threat_intel_service.get_by_indicator(db, data.indicator)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Indicator already exists")
    return await threat_intel_service.create(db, data)


@router.delete("/{indicator}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_indicator(
    indicator: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    entry = await threat_intel_service.get_by_indicator(db, indicator)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Indicator not found")
    await threat_intel_service.delete(db, entry)
