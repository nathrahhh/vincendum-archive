"""create_repayments

Revision ID: 0017_create_repayments
Revises: 0016_add_deal_repayment_terms
Create Date: 2026-08-22

Creates the repayments table for scheduled deal instalments and actual
payment tracking. One deal may have many repayment rows. Does not modify
existing tables or generate schedules.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017_create_repayments"
down_revision: Union[str, None] = "0016_add_deal_repayment_terms"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repayments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("principal_due", sa.Float(), nullable=False),
        sa.Column("interest_due", sa.Float(), nullable=False),
        sa.Column("total_due", sa.Float(), nullable=False),
        sa.Column(
            "principal_paid",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "interest_paid",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_paid",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="SCHEDULED",
        ),
        sa.Column("paid_at", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["deal_id"],
            ["deals.id"],
            name="fk_repayments_deal_id_deals",
        ),
    )
    op.create_index(
        op.f("ix_repayments_deal_id"),
        "repayments",
        ["deal_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_repayments_deal_id"), table_name="repayments")
    op.drop_table("repayments")
