"""Historical no-op: clients.lender_id was already added by 0003.

Revision ID: 0006_restore_client_lender_id
Revises: 0005_add_user_id_to_clients
Create Date: 2026-08-07
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "0006_restore_client_lender_id"
down_revision: Union[str, None] = "0005_add_user_id_to_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Historical migration.
    # clients.lender_id is already created by 0003.
    pass


def downgrade() -> None:
    # No-op because 0003 owns the lender_id schema change.
    pass