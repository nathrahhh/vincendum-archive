"""create_bank_transactions

Revision ID: 0020_create_bank_transactions
Revises: 0019_add_callback_state
Create Date: 2026-08-23

Creates bank_transactions for TrueLayer Open Banking sync. Ownership is
inherited via bank_accounts → bank_connections → clients. Does not store
tokens or credentials.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_create_bank_transactions"
down_revision: Union[str, None] = "0019_add_callback_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bank_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bank_account_id", sa.Integer(), nullable=False),
        sa.Column("truelayer_transaction_id", sa.String(length=255), nullable=False),
        sa.Column("booking_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("value_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amount", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transaction_type", sa.String(length=50), nullable=True),
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
            ["bank_account_id"],
            ["bank_accounts.id"],
            name="fk_bank_transactions_bank_account_id_bank_accounts",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "bank_account_id",
            "truelayer_transaction_id",
            name="uq_bank_transactions_account_truelayer_transaction",
        ),
    )
    op.create_index(
        op.f("ix_bank_transactions_bank_account_id"),
        "bank_transactions",
        ["bank_account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_truelayer_transaction_id"),
        "bank_transactions",
        ["truelayer_transaction_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_bank_transactions_booking_date"),
        "bank_transactions",
        ["booking_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_bank_transactions_booking_date"),
        table_name="bank_transactions",
    )
    op.drop_index(
        op.f("ix_bank_transactions_truelayer_transaction_id"),
        table_name="bank_transactions",
    )
    op.drop_index(
        op.f("ix_bank_transactions_bank_account_id"),
        table_name="bank_transactions",
    )
    op.drop_table("bank_transactions")
