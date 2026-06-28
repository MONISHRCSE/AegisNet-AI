from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.deps import get_current_user, get_current_active_admin
from app.db.postgres import get_db
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.services import asset_service

router = APIRouter()


@router.get("/", response_model=List[AssetResponse])
async def list_assets(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    return await asset_service.get_all(db)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user)
):
    asset = await asset_service.get_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    data: AssetCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    existing = await asset_service.get_by_ip(db, str(data.ip_address))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset with this IP already exists")
    return await asset_service.create(db, data)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    asset = await asset_service.get_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return await asset_service.update(db, asset, data)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_active_admin)
):
    asset = await asset_service.get_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    await asset_service.delete(db, asset)
