"""add_client_financials_client_id_fk

Revision ID: 0023_client_financials_client_fk
Revises: 0022_positions_client_fk
Create Date: 2026-08-29

Adds a proper FK constraint for client_financials.client_id → clients.id.
Aborts if any client_id values do not reference an existing client.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_client_financials_client_fk"
down_revision: Union[str, None] = "0022_positions_client_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    orphans = conn.execute(
        sa.text(
            """
            SELECT cf.id, cf.client_id
            FROM client_financials cf
            LEFT JOIN clients c ON c.id = cf.client_id
            WHERE c.id IS NULL
            ORDER BY cf.id
            """
        )
    ).fetchall()
    if orphans:
        details = ", ".join(
            f"client_financial {row[0]} -> client_id {row[1]}" for row in orphans
        )
        raise RuntimeError(
            "Cannot add FK client_financials.client_id -> clients.id: orphan "
            f"rows exist ({details})."
        )

    op.create_foreign_key(
        "fk_client_financials_client_id_clients",
        "client_financials",
        "clients",
        ["client_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_client_financials_client_id_clients",
        "client_financials",
        type_="foreignkey",
    )
