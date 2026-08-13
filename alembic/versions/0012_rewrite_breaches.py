"""rewrite_breaches_table

Revision ID: 0012_rewrite_breaches
Revises: 0011_add_auditlogs
Create Date: 2026-08-13

Drops and recreates the breaches table to match BreachORM.

Existing breach rows are disposable development data and are not preserved.

New columns:
- lender_id (FK lenders.id, RESTRICT)
- client_id (FK clients.id, RESTRICT)
- threshold / actual_value (replacing limit_pct / actual_pct)
- status (default OPEN)
- resolved_by / resolved_at
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012_rewrite_breaches"
down_revision: Union[str, None] = "0011_add_auditlogs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("breaches")

    op.create_table(
        "breaches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lender_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("rule", sa.String(length=80), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("actual_value", sa.Float(), nullable=False),
        sa.Column("detail", sa.String(length=500), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="OPEN",
        ),
        sa.Column("resolved_by", sa.Integer(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_breaches_lender_id_lenders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            name="fk_breaches_client_id_clients",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["resolved_by"],
            ["users.id"],
            name="fk_breaches_resolved_by_users",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(op.f("ix_breaches_id"), "breaches", ["id"], unique=False)
    op.create_index(
        op.f("ix_breaches_lender_id"),
        "breaches",
        ["lender_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_client_id"),
        "breaches",
        ["client_id"],
        unique=False,
    )
    op.create_index(op.f("ix_breaches_rule"), "breaches", ["rule"], unique=False)
    op.create_index(
        op.f("ix_breaches_reason"),
        "breaches",
        ["reason"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_industry"),
        "breaches",
        ["industry"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_status"),
        "breaches",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_resolved_by"),
        "breaches",
        ["resolved_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_breaches_resolved_by"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_status"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_industry"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_reason"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_rule"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_client_id"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_lender_id"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_id"), table_name="breaches")
    op.drop_table("breaches")

    # Restore the previous baseline breaches shape (pre-rewrite).
    op.create_table(
        "breaches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule", sa.String(length=80), nullable=False),
        sa.Column("limit_pct", sa.Float(), nullable=False),
        sa.Column("actual_pct", sa.Float(), nullable=False),
        sa.Column("detail", sa.String(length=500), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
    )
    op.create_index(op.f("ix_breaches_id"), "breaches", ["id"], unique=False)
    op.create_index(op.f("ix_breaches_rule"), "breaches", ["rule"], unique=False)
    op.create_index(
        op.f("ix_breaches_reason"),
        "breaches",
        ["reason"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_industry"),
        "breaches",
        ["industry"],
        unique=False,
    )
