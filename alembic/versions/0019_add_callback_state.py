"""add_bank_connection_callback_state

Revision ID: 0019_add_bank_connection_callback_state
Revises: 0018_create_bank_connections
Create Date: 2026-08-23

Adds bank_connections.callback_state so the Open Banking return_uri can carry
a Vincendum-owned correlator. TrueLayer Data V3 does not document callback
query parameters on return_uri; status is confirmed via provider API access.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_add_callback_state"
down_revision: Union[str, None] = "0018_create_bank_connections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bank_connections",
        sa.Column("callback_state", sa.String(length=64), nullable=True),
    )
    op.create_index(
        op.f("ix_bank_connections_callback_state"),
        "bank_connections",
        ["callback_state"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_bank_connections_callback_state"),
        table_name="bank_connections",
    )
    op.drop_column("bank_connections", "callback_state")
