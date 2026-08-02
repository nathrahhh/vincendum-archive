"""create_lenders_users_client_applications

Revision ID: 0002_create_lenders_users_client_applications
Revises: 0001_baseline_existing_schema
Create Date: 2026-08-02

Creates new multi-tenant tables:
- lenders
- users
- client_applications

Does not modify existing baseline tables:
- clients
- client_financials
- deals
- positions
- breaches
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0002_create_lenders_users_client_applications"
down_revision: Union[str, None] = "0001_baseline_existing_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lenders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        op.f("ix_lenders_id"),
        "lenders",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_lenders_name"),
        "lenders",
        ["name"],
        unique=False,
    )


    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "lender_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_users_lender_id_lenders",
        ),
        sa.UniqueConstraint(
            "email",
            name="uq_users_email",
        ),
    )

    op.create_index(
        op.f("ix_users_id"),
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_email"),
        "users",
        ["email"],
        unique=True,
    )

    op.create_index(
        op.f("ix_users_role"),
        "users",
        ["role"],
        unique=False,
    )

    op.create_index(
        op.f("ix_users_lender_id"),
        "users",
        ["lender_id"],
        unique=False,
    )


    op.create_table(
        "client_applications",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "lender_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "industry",
            sa.String(length=120),
            nullable=False,
        ),
        sa.Column(
            "credit_limit",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_client_applications_lender_id_lenders",
        ),
    )

    op.create_index(
        op.f("ix_client_applications_id"),
        "client_applications",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_client_applications_lender_id"),
        "client_applications",
        ["lender_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_client_applications_name"),
        "client_applications",
        ["name"],
        unique=False,
    )

    op.create_index(
        op.f("ix_client_applications_industry"),
        "client_applications",
        ["industry"],
        unique=False,
    )

    op.create_index(
        op.f("ix_client_applications_status"),
        "client_applications",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_client_applications_status"),
        table_name="client_applications",
    )

    op.drop_index(
        op.f("ix_client_applications_industry"),
        table_name="client_applications",
    )

    op.drop_index(
        op.f("ix_client_applications_name"),
        table_name="client_applications",
    )

    op.drop_index(
        op.f("ix_client_applications_lender_id"),
        table_name="client_applications",
    )

    op.drop_index(
        op.f("ix_client_applications_id"),
        table_name="client_applications",
    )

    op.drop_table("client_applications")


    op.drop_index(
        op.f("ix_users_lender_id"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_role"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_email"),
        table_name="users",
    )

    op.drop_index(
        op.f("ix_users_id"),
        table_name="users",
    )

    op.drop_table("users")


    op.drop_index(
        op.f("ix_lenders_name"),
        table_name="lenders",
    )

    op.drop_index(
        op.f("ix_lenders_id"),
        table_name="lenders",
    )

    op.drop_table("lenders")