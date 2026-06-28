from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import List
from app.db.models import IndicatorType

class ThreatIntelligenceBase(BaseModel):
    indicator: str
    indicator_type: IndicatorType
    source: str
    confidence_score: int = Field(..., ge=0, le=100)
    tags: List[str] = []

class ThreatIntelligenceCreate(ThreatIntelligenceBase):
    pass

class ThreatIntelligenceUpdate(ThreatIntelligenceBase):
    indicator: str | None = None
    indicator_type: IndicatorType | None = None
    source: str | None = None
    confidence_score: int | None = Field(default=None, ge=0, le=100)

class ThreatIntelligenceResponse(ThreatIntelligenceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
