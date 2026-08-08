"""add client_id to users

Revision ID: d1cb90780c7f
Revises: 0006_restore_client_lender_id
Create Date: 2026-08-08 09:13:20.894093
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0007_add_client_id_to_users' 
down_revision: Union[str, None] = '0006_restore_client_lender_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("client_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_users_client_id_clients",
        "users",
        "clients",
        ["client_id"],
        ["id"],
    )

    op.drop_constraint(
        "fk_clients_user_id_users",
        "clients",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_clients_user_id",
        table_name="clients",
    )

    op.drop_column("clients", "user_id")


def downgrade() -> None:
    op.add_column(
        "clients",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_clients_user_id",
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

    op.drop_constraint(
        "fk_users_client_id_clients",
        "users",
        type_="foreignkey",
    )

    op.drop_column("users", "client_id")