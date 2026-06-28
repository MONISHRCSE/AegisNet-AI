from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.role import RoleResponse

class UserBase(BaseModel):
    username: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    role_id: int

class UserUpdate(UserBase):
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    role_id: int | None = None

class UserResponse(UserBase):
    id: UUID
    role_id: int
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime
    role: RoleResponse | None = None

    model_config = ConfigDict(from_attributes=True)
