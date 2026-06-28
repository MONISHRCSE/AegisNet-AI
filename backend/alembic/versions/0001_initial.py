"""initial schema — roles, users, assets, honeypots, threat_intel

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Custom ENUM types ────────────────────────────────────────────────────────
decoy_status_enum    = sa.Enum("pending", "running", "stopped", "archived",   name="decoystatus")
indicator_type_enum  = sa.Enum("ip", "domain", "hash",                        name="indicatortype")
interaction_level_enum = sa.Enum("low", "medium", "high",                     name="interactionlevel")


def upgrade() -> None:
    # ── Enable PostgreSQL extensions ─────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')  # gen_random_uuid()
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')    # case-insensitive text

    # ── roles ─────────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id",          sa.Integer(),    primary_key=True, autoincrement=True),
        sa.Column("name",        sa.String(50),   nullable=False, unique=True),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id",            postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username",      sa.String(100),  nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255),  nullable=False),
        sa.Column("is_active",     sa.Boolean(),    nullable=False, server_default=sa.text("true")),
        sa.Column("last_login",    sa.DateTime(timezone=True), nullable=True),
        sa.Column("role_id",       sa.Integer(),    sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_users_username", "users", ["username"])

    # ── assets ────────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id",                postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("ip_address",        postgresql.INET(),   nullable=False, unique=True),
        sa.Column("mac_address",       postgresql.MACADDR(),nullable=True),
        sa.Column("hostname",          sa.String(255),      nullable=True),
        sa.Column("os_fingerprint",    sa.String(100),      nullable=True),
        sa.Column("criticality_score", sa.Float(),          nullable=False, server_default="1.0"),
        sa.Column("is_honeypot",       sa.Boolean(),        nullable=False, server_default=sa.text("false")),
        sa.Column("last_seen",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at",        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_assets_ip", "assets", ["ip_address"])

    # ── honeypot_templates ────────────────────────────────────────────────────
    op.create_table(
        "honeypot_templates",
        sa.Column("id",                sa.Integer(),        primary_key=True, autoincrement=True),
        sa.Column("name",              sa.String(100),      nullable=False, unique=True),
        sa.Column("docker_image",      sa.String(255),      nullable=False),
        sa.Column("target_ports",      postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("interaction_level", interaction_level_enum, nullable=False),
        sa.Column("env_vars",          postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default="{}"),
        sa.Column("created_at",        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",        sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_honeypot_templates_name", "honeypot_templates", ["name"])

    # ── active_decoys ─────────────────────────────────────────────────────────
    op.create_table(
        "active_decoys",
        sa.Column("id",                 postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("assigned_ip",        postgresql.INET(),   nullable=False),
        sa.Column("target_attacker_ip", postgresql.INET(),   nullable=False),
        sa.Column("status",             decoy_status_enum,   nullable=False, server_default="pending"),
        sa.Column("terminated_at",      sa.DateTime(timezone=True), nullable=True),
        sa.Column("template_id",        sa.Integer(),        sa.ForeignKey("honeypot_templates.id"), nullable=False),
        sa.Column("created_at",         sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",         sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_attacker_ip_status", "active_decoys", ["target_attacker_ip", "status"])

    # ── threat_intelligence ───────────────────────────────────────────────────
    op.create_table(
        "threat_intelligence",
        sa.Column("id",               postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("indicator",        sa.String(255),     nullable=False, unique=True),
        sa.Column("indicator_type",   indicator_type_enum, nullable=False),
        sa.Column("source",           sa.String(100),     nullable=False),
        sa.Column("confidence_score", sa.Integer(),       nullable=False),
        sa.Column("tags",             postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_threat_intel_indicator", "threat_intelligence", ["indicator"])
    op.create_index("idx_threat_intel_type",      "threat_intelligence", ["indicator_type"])

    # ── Seed default roles ────────────────────────────────────────────────────
    op.execute("""
        INSERT INTO roles (name, permissions) VALUES
        ('Admin',   '{"alerts": "rw", "assets": "rw", "honeypots": "rw", "response": "rw", "users": "rw"}'::jsonb),
        ('Analyst', '{"alerts": "rw", "assets": "r",  "honeypots": "r",  "response": "r",  "users": "none"}'::jsonb),
        ('Viewer',  '{"alerts": "r",  "assets": "r",  "honeypots": "r",  "response": "none","users": "none"}'::jsonb)
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.drop_table("threat_intelligence")
    op.drop_index("idx_attacker_ip_status", table_name="active_decoys")
    op.drop_table("active_decoys")
    op.drop_index("idx_honeypot_templates_name", table_name="honeypot_templates")
    op.drop_table("honeypot_templates")
    op.drop_index("idx_assets_ip", table_name="assets")
    op.drop_table("assets")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_table("users")
    op.drop_table("roles")

    indicator_type_enum.drop(op.get_bind(), checkfirst=True)
    interaction_level_enum.drop(op.get_bind(), checkfirst=True)
    decoy_status_enum.drop(op.get_bind(), checkfirst=True)
