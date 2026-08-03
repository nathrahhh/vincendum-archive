"""auth0_user_id_and_nullable_lender_on_users

Revision ID: 0004_users_auth0_nullable_lender
Revises: 0003_add_lender_id_to_clients
Create Date: 2026-08-03

Updates the existing users table for Auth0-based auth:
- drop password_hash
- add auth0_user_id (NOT NULL, unique, indexed)
- make lender_id nullable

Does not recreate users or modify other tables.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_users_auth0_nullable_lender"
down_revision: Union[str, None] = "0003_add_lender_id_to_clients"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Stage 1: add nullable column so existing rows are preserved.
    op.add_column(
        "users",
        sa.Column("auth0_user_id", sa.String(length=255), nullable=True),
    )

    # Stage 2: backfill unique placeholders for any existing users.
    # Replace these with real Auth0 `sub` values after cutover.
    op.execute(
        sa.text(
            "UPDATE users "
            "SET auth0_user_id = 'pending:' || id::text "
            "WHERE auth0_user_id IS NULL"
        )
    )

    # Stage 3: enforce NOT NULL + unique index.
    op.alter_column(
        "users",
        "auth0_user_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.create_index(
        op.f("ix_users_auth0_user_id"),
        "users",
        ["auth0_user_id"],
        unique=True,
    )

    op.drop_column("users", "password_hash")

    op.alter_column(
        "users",
        "lender_id",
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade() -> None:
    # Restore NOT NULL lender_id only after clearing nulls.
    op.execute(
        sa.text(
            "UPDATE users "
            "SET lender_id = (SELECT id FROM lenders ORDER BY id LIMIT 1) "
            "WHERE lender_id IS NULL"
        )
    )
    op.alter_column(
        "users",
        "lender_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column("users", "password_hash", server_default=None)

    op.drop_index(op.f("ix_users_auth0_user_id"), table_name="users")
    op.drop_column("users", "auth0_user_id")
