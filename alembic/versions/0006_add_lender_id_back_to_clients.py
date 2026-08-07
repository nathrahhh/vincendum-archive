"""add lender id back to clients

Revision ID: 01b493a4f2f5
Revises: 0005_add_user_id_to_clients
Create Date: 2026-08-07 16:54:25.270648
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_add_lender_id_back_to_clients"
down_revision: Union[str, None] = "0005_add_user_id_to_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("lender_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        op.f("ix_clients_lender_id"),
        "clients",
        ["lender_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_clients_lender_id_lenders",
        "clients",
        "lenders",
        ["lender_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_clients_lender_id_lenders",
        "clients",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_clients_lender_id"),
        table_name="clients",
    )

    op.drop_column(
        "clients",
        "lender_id",
    )
