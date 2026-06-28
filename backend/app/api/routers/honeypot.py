from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.deps import get_current_user, get_current_active_admin
from app.db.postgres import get_db
from app.schemas.honeypot import (
    HoneypotTemplateCreate, HoneypotTemplateResponse,
    ActiveDecoyCreate, ActiveDecoyResponse
)
from app.services import honeypot_service

router = APIRouter()


# --- Templates ---

@router.get("/templates", response_model=List[HoneypotTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    return await honeypot_service.get_all_templates(db)


@router.post("/templates", response_model=HoneypotTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: HoneypotTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    return await honeypot_service.create_template(db, data)


# --- Active Decoys ---

@router.get("/decoys", response_model=List[ActiveDecoyResponse])
async def list_decoys(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    return await honeypot_service.get_all_decoys(db)


@router.post("/decoys", response_model=ActiveDecoyResponse, status_code=status.HTTP_201_CREATED)
async def deploy_decoy(
    data: ActiveDecoyCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    existing = await honeypot_service.get_active_decoy_by_attacker_ip(db, str(data.target_attacker_ip))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active decoy already targets {data.target_attacker_ip}"
        )
    return await honeypot_service.create_decoy(db, data)


@router.post("/decoys/{decoy_id}/terminate", response_model=ActiveDecoyResponse)
async def terminate_decoy(
    decoy_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    decoy = await honeypot_service.get_decoy_by_id(db, decoy_id)
    if not decoy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decoy not found")
    return await honeypot_service.terminate_decoy(db, decoy)
