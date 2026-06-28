from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.models import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


async def get_all(db: AsyncSession) -> List[Asset]:
    result = await db.execute(select(Asset).order_by(Asset.created_at.desc()))
    return result.scalars().all()


async def get_by_id(db: AsyncSession, asset_id: UUID) -> Asset | None:
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()


async def get_by_ip(db: AsyncSession, ip: str) -> Asset | None:
    result = await db.execute(select(Asset).where(Asset.ip_address == ip))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: AssetCreate) -> Asset:
    asset = Asset(**data.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def update(db: AsyncSession, asset: Asset, data: AssetUpdate) -> Asset:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete(db: AsyncSession, asset: Asset) -> None:
    await db.delete(asset)
    await db.commit()
