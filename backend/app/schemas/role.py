from pydantic import BaseModel, ConfigDict
from typing import Dict, Any

class RoleBase(BaseModel):
    name: str
    permissions: Dict[str, Any] = {}

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    name: str | None = None
    permissions: Dict[str, Any] | None = None

class RoleResponse(RoleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
