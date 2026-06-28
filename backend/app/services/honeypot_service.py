from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.db.models import HoneypotTemplate, ActiveDecoy, DecoyStatus
from app.schemas.honeypot import HoneypotTemplateCreate, ActiveDecoyCreate, ActiveDecoyUpdate
from datetime import datetime, timezone


async def get_all_templates(db: AsyncSession) -> List[HoneypotTemplate]:
    result = await db.execute(select(HoneypotTemplate))
    return result.scalars().all()


async def get_template_by_id(db: AsyncSession, template_id: int) -> HoneypotTemplate | None:
    result = await db.execute(select(HoneypotTemplate).where(HoneypotTemplate.id == template_id))
    return result.scalar_one_or_none()


async def create_template(db: AsyncSession, data: HoneypotTemplateCreate) -> HoneypotTemplate:
    template = HoneypotTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


async def get_all_decoys(db: AsyncSession) -> List[ActiveDecoy]:
    result = await db.execute(
        select(ActiveDecoy)
        .options(selectinload(ActiveDecoy.template))
        .order_by(ActiveDecoy.created_at.desc())
    )
    return result.scalars().all()


async def get_decoy_by_id(db: AsyncSession, decoy_id: UUID) -> ActiveDecoy | None:
    result = await db.execute(
        select(ActiveDecoy)
        .options(selectinload(ActiveDecoy.template))
        .where(ActiveDecoy.id == decoy_id)
    )
    return result.scalar_one_or_none()


async def get_active_decoy_by_attacker_ip(db: AsyncSession, attacker_ip: str) -> ActiveDecoy | None:
    result = await db.execute(
        select(ActiveDecoy).where(
            ActiveDecoy.target_attacker_ip == attacker_ip,
            ActiveDecoy.status == DecoyStatus.RUNNING
        )
    )
    return result.scalar_one_or_none()


async def create_decoy(db: AsyncSession, data: ActiveDecoyCreate) -> ActiveDecoy:
    decoy = ActiveDecoy(**data.model_dump())
    db.add(decoy)
    await db.commit()
    await db.refresh(decoy)
    return decoy


async def terminate_decoy(db: AsyncSession, decoy: ActiveDecoy) -> ActiveDecoy:
    decoy.status = DecoyStatus.STOPPED
    decoy.terminated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(decoy)
    return decoy
