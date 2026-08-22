"""add_deal_repayment_terms

Revision ID: 0016_add_deal_repayment_terms
Revises: 0015_add_lender_slug
Create Date: 2026-08-22

Adds optional repayment-term columns to deals. All columns are nullable so
existing deal rows remain valid. String fields with application defaults
receive DB defaults for future inserts only (existing rows stay NULL).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016_add_deal_repayment_terms"
down_revision: Union[str, None] = "0015_add_lender_slug"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "deals",
        sa.Column("principal_amount", sa.Float(), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("interest_rate", sa.Float(), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("interest_rate_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("repayment_method", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("term_months", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("start_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("maturity_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("payment_frequency", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "deals",
        sa.Column("first_payment_date", sa.Date(), nullable=True),
    )

    # Defaults apply to future inserts only; existing NULL rows are unchanged.
    op.alter_column(
        "deals",
        "interest_rate_type",
        server_default="fixed",
    )
    op.alter_column(
        "deals",
        "repayment_method",
        server_default="amortizing",
    )
    op.alter_column(
        "deals",
        "payment_frequency",
        server_default="monthly",
    )


def downgrade() -> None:
    op.drop_column("deals", "first_payment_date")
    op.drop_column("deals", "payment_frequency")
    op.drop_column("deals", "maturity_date")
    op.drop_column("deals", "start_date")
    op.drop_column("deals", "term_months")
    op.drop_column("deals", "repayment_method")
    op.drop_column("deals", "interest_rate_type")
    op.drop_column("deals", "interest_rate")
    op.drop_column("deals", "principal_amount")
