from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, IPvAnyAddress
from typing import List, Dict, Any
from app.db.models import InteractionLevel, DecoyStatus

class HoneypotTemplateBase(BaseModel):
    name: str
    docker_image: str
    target_ports: List[int]
    interaction_level: InteractionLevel
    env_vars: Dict[str, Any] = {}

class HoneypotTemplateCreate(HoneypotTemplateBase):
    pass

class HoneypotTemplateUpdate(HoneypotTemplateBase):
    name: str | None = None
    docker_image: str | None = None
    target_ports: List[int] | None = None
    interaction_level: InteractionLevel | None = None

class HoneypotTemplateResponse(HoneypotTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActiveDecoyBase(BaseModel):
    assigned_ip: IPvAnyAddress
    target_attacker_ip: IPvAnyAddress
    status: DecoyStatus = DecoyStatus.PENDING

class ActiveDecoyCreate(ActiveDecoyBase):
    template_id: int

class ActiveDecoyUpdate(ActiveDecoyBase):
    assigned_ip: IPvAnyAddress | None = None
    target_attacker_ip: IPvAnyAddress | None = None
    status: DecoyStatus | None = None

class ActiveDecoyResponse(ActiveDecoyBase):
    id: UUID
    template_id: int
    terminated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    template: HoneypotTemplateResponse | None = None

    model_config = ConfigDict(from_attributes=True)
