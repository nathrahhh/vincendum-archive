"""create_bank_connections_and_accounts

Revision ID: 0018_create_bank_connections_and_accounts
Revises: 0017_create_repayments
Create Date: 2026-08-22

Creates bank_connections and bank_accounts for TrueLayer Open Banking
ownership. Lender tenancy is derived via clients.lender_id. Does not
store tokens, credentials, or transaction history.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018_create_bank_connections"
down_revision: Union[str, None] = "0017_create_repayments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bank_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("truelayer_connection_id", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            name="fk_bank_connections_client_id_clients",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "truelayer_connection_id",
            name="uq_bank_connections_truelayer_connection_id",
        ),
    )
    op.create_index(
        op.f("ix_bank_connections_client_id"),
        "bank_connections",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_connections_truelayer_connection_id"),
        "bank_connections",
        ["truelayer_connection_id"],
        unique=False,
    )

    op.create_table(
        "bank_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bank_connection_id", sa.Integer(), nullable=False),
        sa.Column("truelayer_account_id", sa.String(length=255), nullable=False),
        sa.Column("account_type", sa.String(length=50), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bank_connection_id"],
            ["bank_connections.id"],
            name="fk_bank_accounts_bank_connection_id_bank_connections",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "bank_connection_id",
            "truelayer_account_id",
            name="uq_bank_accounts_connection_truelayer_account",
        ),
    )
    op.create_index(
        op.f("ix_bank_accounts_bank_connection_id"),
        "bank_accounts",
        ["bank_connection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_accounts_truelayer_account_id"),
        "bank_accounts",
        ["truelayer_account_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_bank_accounts_truelayer_account_id"),
        table_name="bank_accounts",
    )
    op.drop_index(
        op.f("ix_bank_accounts_bank_connection_id"),
        table_name="bank_accounts",
    )
    op.drop_table("bank_accounts")

    op.drop_index(
        op.f("ix_bank_connections_truelayer_connection_id"),
        table_name="bank_connections",
    )
    op.drop_index(
        op.f("ix_bank_connections_client_id"),
        table_name="bank_connections",
    )
    op.drop_table("bank_connections")
