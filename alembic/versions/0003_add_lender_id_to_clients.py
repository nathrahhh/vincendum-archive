"""add_lender_id_to_clients

Revision ID: 0003_add_lender_id_to_clients
Revises: 0002_create_lenders_users_client_applications
Create Date: 2026-08-02

Adds nullable lender_id to the existing clients table only.
Does not modify client_financials, deals, positions, or breaches.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_lender_id_to_clients"
down_revision: Union[str, None] = "0002_create_lenders_users_client_applications"
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
    op.drop_index(op.f("ix_clients_lender_id"), table_name="clients")
    op.drop_column("clients", "lender_id")
