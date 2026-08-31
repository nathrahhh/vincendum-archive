"""add_positions_client_id_fk

Revision ID: 0022_positions_client_fk
Revises: 0021_create_portfolios
Create Date: 2026-08-29

Adds a proper FK constraint for positions.client_id → clients.id.
The column remains nullable. Aborts if any non-null client_id values
do not reference an existing client.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_positions_client_fk"
down_revision: Union[str, None] = "0021_create_portfolios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    orphans = conn.execute(
        sa.text(
            """
            SELECT p.id, p.client_id
            FROM positions p
            LEFT JOIN clients c ON c.id = p.client_id
            WHERE p.client_id IS NOT NULL
              AND c.id IS NULL
            ORDER BY p.id
            """
        )
    ).fetchall()
    if orphans:
        details = ", ".join(
            f"position {row[0]} -> client_id {row[1]}" for row in orphans
        )
        raise RuntimeError(
            "Cannot add FK positions.client_id -> clients.id: orphan "
            f"positions exist ({details})."
        )

    op.create_foreign_key(
        "fk_positions_client_id_clients",
        "positions",
        "clients",
        ["client_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_positions_client_id_clients",
        "positions",
        type_="foreignkey",
    )
