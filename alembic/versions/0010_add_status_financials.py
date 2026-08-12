"""add_status_to_client_financials

Revision ID: 0010_add_status_to_client_financials
Revises: 0009_deal_fk
Create Date: 2026-08-12

Adds client_financials.status (VARCHAR(50), NOT NULL) for the same
PENDING / APPROVED / REJECTED review workflow used by deals.

Existing rows are backfilled to PENDING. No other tables are modified.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010_add_status_financials"
down_revision: Union[str, None] = "0009_deal_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default fills existing rows so NOT NULL can be applied safely.
    op.add_column(
        "client_financials",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="PENDING",
        ),
    )
    # Match DealORM: application default only, no permanent DB default.
    op.alter_column("client_financials", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("client_financials", "status")
