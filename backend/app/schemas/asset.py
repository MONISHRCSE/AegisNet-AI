from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, IPvAnyAddress, Field

class AssetBase(BaseModel):
    ip_address: IPvAnyAddress
    mac_address: str | None = None
    hostname: str | None = None
    os_fingerprint: str | None = None
    criticality_score: float = Field(default=1.0, ge=0.0, le=10.0)
    is_honeypot: bool = False

class AssetCreate(AssetBase):
    pass

class AssetUpdate(AssetBase):
    ip_address: IPvAnyAddress | None = None
    criticality_score: float | None = Field(default=None, ge=0.0, le=10.0)
    is_honeypot: bool | None = None

class AssetResponse(AssetBase):
    id: UUID
    last_seen: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
