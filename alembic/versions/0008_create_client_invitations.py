"""create_client_invitations

Revision ID: 0008_create_client_invitations
Revises: 0007_add_client_id_to_users
Create Date: 2026-08-10

Adds the client_invitations table for lender-issued client invites.
Does not modify existing tables or production data.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_create_client_invitations"
down_revision: Union[str, None] = "0007_add_client_id_to_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_invitations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lender_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_client_invitations_lender_id_lenders",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            name="fk_client_invitations_client_id_clients",
        ),
    )
    op.create_index(
        op.f("ix_client_invitations_id"),
        "client_invitations",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_invitations_lender_id"),
        "client_invitations",
        ["lender_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_invitations_client_id"),
        "client_invitations",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_invitations_email"),
        "client_invitations",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_invitations_token_hash"),
        "client_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_client_invitations_status"),
        "client_invitations",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_client_invitations_status"),
        table_name="client_invitations",
    )
    op.drop_index(
        op.f("ix_client_invitations_token_hash"),
        table_name="client_invitations",
    )
    op.drop_index(
        op.f("ix_client_invitations_email"),
        table_name="client_invitations",
    )
    op.drop_index(
        op.f("ix_client_invitations_client_id"),
        table_name="client_invitations",
    )
    op.drop_index(
        op.f("ix_client_invitations_lender_id"),
        table_name="client_invitations",
    )
    op.drop_index(
        op.f("ix_client_invitations_id"),
        table_name="client_invitations",
    )
    op.drop_table("client_invitations")
