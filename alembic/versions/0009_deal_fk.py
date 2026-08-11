"""drop_deal_industry_require_client_id

Revision ID: 0009_drop_deal_industry_require_client_id
Revises: 0008_create_client_invitations
Create Date: 2026-08-11

Removes deals.industry (industry lives on clients) and requires deals.client_id
with a foreign key to clients.id.

Preserves existing deal rows. Aborts if any deal has NULL client_id or
references a missing client, rather than deleting or rewriting data.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_deal_fk"
down_revision: Union[str, None] = "0008_create_client_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    null_client_ids = conn.execute(
        sa.text("SELECT id FROM deals WHERE client_id IS NULL ORDER BY id")
    ).fetchall()
    if null_client_ids:
        ids = ", ".join(str(row[0]) for row in null_client_ids)
        raise RuntimeError(
            "Cannot make deals.client_id NOT NULL: deals with NULL client_id "
            f"exist (ids: {ids}). Resolve or backfill these rows first; "
            "this migration will not delete or modify them."
        )

    orphans = conn.execute(
        sa.text(
            """
            SELECT d.id, d.client_id
            FROM deals d
            LEFT JOIN clients c ON c.id = d.client_id
            WHERE c.id IS NULL
            ORDER BY d.id
            """
        )
    ).fetchall()
    if orphans:
        details = ", ".join(f"deal {row[0]} -> client_id {row[1]}" for row in orphans)
        raise RuntimeError(
            "Cannot add FK deals.client_id -> clients.id: orphan deals exist "
            f"({details}). Resolve missing clients first; this migration will "
            "not delete or rewrite deal rows."
        )

    op.drop_index(op.f("ix_deals_industry"), table_name="deals")
    op.drop_column("deals", "industry")

    op.alter_column(
        "deals",
        "client_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_index(
        op.f("ix_deals_client_id"),
        "deals",
        ["client_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_deals_client_id_clients",
        "deals",
        "clients",
        ["client_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_deals_client_id_clients", "deals", type_="foreignkey")
    op.drop_index(op.f("ix_deals_client_id"), table_name="deals")
    op.alter_column(
        "deals",
        "client_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "deals",
        sa.Column("industry", sa.String(length=120), nullable=True),
    )
    op.execute(
        sa.text(
            """
            UPDATE deals AS d
            SET industry = c.industry
            FROM clients AS c
            WHERE d.client_id = c.id AND d.industry IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE deals
            SET industry = 'Unknown'
            WHERE industry IS NULL
            """
        )
    )
    op.alter_column(
        "deals",
        "industry",
        existing_type=sa.String(length=120),
        nullable=False,
    )
    op.create_index(
        op.f("ix_deals_industry"),
        "deals",
        ["industry"],
        unique=False,
    )
