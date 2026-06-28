from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.db.models import ThreatIntelligence
from app.schemas.threat_intel import ThreatIntelligenceCreate


async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ThreatIntelligence]:
    result = await db.execute(
        select(ThreatIntelligence).offset(skip).limit(limit).order_by(ThreatIntelligence.created_at.desc())
    )
    return result.scalars().all()


async def get_by_indicator(db: AsyncSession, indicator: str) -> ThreatIntelligence | None:
    result = await db.execute(
        select(ThreatIntelligence).where(ThreatIntelligence.indicator == indicator)
    )
    return result.scalar_one_or_none()


async def create(db: AsyncSession, data: ThreatIntelligenceCreate) -> ThreatIntelligence:
    entry = ThreatIntelligence(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete(db: AsyncSession, entry: ThreatIntelligence) -> None:
    await db.delete(entry)
    await db.commit()
