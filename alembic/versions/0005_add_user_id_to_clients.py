"""add_user_id_to_clients

Revision ID: 0005_add_user_id_to_clients
Revises: 0004_users_auth0_nullable_lender
Create Date: 2026-08-03

Adds clients.user_id → users.id (unique) so each client profile maps to
exactly one UserORM.

Existing client rows have no owning user yet, so user_id is added as
nullable in this migration. After manual/backfill assignment, a follow-up
migration should set NOT NULL to match ClientORM.user_id.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_user_id_to_clients"
down_revision: Union[str, None] = "0004_users_auth0_nullable_lender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable for existing production clients until user ownership is backfilled.
    # Target ORM contract is NOT NULL + unique once every row has a user_id.
    op.add_column(
        "clients",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_clients_user_id"),
        "clients",
        ["user_id"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_clients_user_id_users",
        "clients",
        "users",
        ["user_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_clients_user_id_users",
        "clients",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_clients_user_id"), table_name="clients")
    op.drop_column("clients", "user_id")
