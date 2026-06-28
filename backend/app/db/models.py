import uuid
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String, Boolean, DateTime, Float, ForeignKey, Integer, Enum, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET, MACADDR, JSONB, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )

class DecoyStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    ARCHIVED = "archived"

class IndicatorType(str, enum.Enum):
    IP = "ip"
    DOMAIN = "domain"
    HASH = "hash"

class InteractionLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    users: Mapped[List["User"]] = relationship("User", back_populates="role")

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role: Mapped["Role"] = relationship("Role", back_populates="users")

class Asset(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assets"
    
    ip_address: Mapped[str] = mapped_column(INET, unique=True, index=True, nullable=False)
    mac_address: Mapped[Optional[str]] = mapped_column(MACADDR, nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    os_fingerprint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    criticality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_honeypot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class HoneypotTemplate(Base, TimestampMixin):
    __tablename__ = "honeypot_templates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    docker_image: Mapped[str] = mapped_column(String(255), nullable=False)
    target_ports: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    interaction_level: Mapped[InteractionLevel] = mapped_column(Enum(InteractionLevel), nullable=False)
    env_vars: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)
    
    active_decoys: Mapped[List["ActiveDecoy"]] = relationship("ActiveDecoy", back_populates="template")

class ActiveDecoy(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "active_decoys"
    
    assigned_ip: Mapped[str] = mapped_column(INET, nullable=False)
    target_attacker_ip: Mapped[str] = mapped_column(INET, index=True, nullable=False)
    status: Mapped[DecoyStatus] = mapped_column(Enum(DecoyStatus), default=DecoyStatus.PENDING, nullable=False)
    terminated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    template_id: Mapped[int] = mapped_column(ForeignKey("honeypot_templates.id"), nullable=False)
    template: Mapped["HoneypotTemplate"] = relationship("HoneypotTemplate", back_populates="active_decoys")

    __table_args__ = (
        Index("idx_attacker_ip_status", "target_attacker_ip", "status"),
    )

class ThreatIntelligence(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "threat_intelligence"
    
    indicator: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    indicator_type: Mapped[IndicatorType] = mapped_column(Enum(IndicatorType), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String), nullable=True)

    __table_args__ = (
        Index("idx_indicator_type", "indicator_type"),
    )
