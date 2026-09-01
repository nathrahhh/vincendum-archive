"""Initial baseline schema for pre-Alembic tables.

Revision ID: 0001_baseline_existing_schema
Revises:
Create Date: 2026-08-01

Creates the five tables that existed before incremental migrations began:

- clients
- client_financials
- deals
- positions
- breaches

Schema reflects the state immediately before ``0002`` (reconstructed from
later migrations' upgrade/downgrade steps and ORM history). Later columns such
as ``clients.lender_id``, ``deals`` repayment terms, ``client_financials.status``,
``positions.portfolio_id`` / ``positions.deal_id``, and the post-``0012`` breach
shape are added by subsequent revisions.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_baseline_existing_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=False),
        sa.Column("credit_limit", sa.Float(), nullable=False),
    )
    op.create_index(op.f("ix_clients_id"), "clients", ["id"], unique=False)
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=False)
    op.create_index(
        op.f("ix_clients_industry"),
        "clients",
        ["industry"],
        unique=False,
    )

    op.create_table(
        "client_financials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("revenue", sa.Float(), nullable=False),
        sa.Column("cogs", sa.Float(), nullable=False),
        sa.Column("gross_profit", sa.Float(), nullable=False),
        sa.Column("opex", sa.Float(), nullable=False),
        sa.Column("cash_balance", sa.Float(), nullable=False),
    )
    op.create_index(
        op.f("ix_client_financials_id"),
        "client_financials",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_financials_client_id"),
        "client_financials",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_client_financials_month"),
        "client_financials",
        ["month"],
        unique=False,
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=False),
    )
    op.create_index(op.f("ix_deals_id"), "deals", ["id"], unique=False)
    op.create_index(op.f("ix_deals_name"), "deals", ["name"], unique=False)
    op.create_index(
        op.f("ix_deals_industry"),
        "deals",
        ["industry"],
        unique=False,
    )

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("industry", sa.String(length=120), nullable=False),
    )
    op.create_index(op.f("ix_positions_id"), "positions", ["id"], unique=False)
    op.create_index(
        op.f("ix_positions_name"),
        "positions",
        ["name"],
        unique=True,
    )
    op.create_index(
        op.f("ix_positions_industry"),
        "positions",
        ["industry"],
        unique=False,
    )

    op.create_table(
        "breaches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rule", sa.String(length=80), nullable=False),
        sa.Column("limit_pct", sa.Float(), nullable=False),
        sa.Column("actual_pct", sa.Float(), nullable=False),
        sa.Column("detail", sa.String(length=500), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=120), nullable=True),
    )
    op.create_index(op.f("ix_breaches_id"), "breaches", ["id"], unique=False)
    op.create_index(op.f("ix_breaches_rule"), "breaches", ["rule"], unique=False)
    op.create_index(
        op.f("ix_breaches_reason"),
        "breaches",
        ["reason"],
        unique=False,
    )
    op.create_index(
        op.f("ix_breaches_industry"),
        "breaches",
        ["industry"],
        unique=False,
    )

    # Alembic defaults to VARCHAR(32); later revisions use longer revision ids.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("alembic_version"):
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(length=32),
            type_=sa.String(length=128),
            existing_nullable=False,
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_breaches_industry"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_reason"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_rule"), table_name="breaches")
    op.drop_index(op.f("ix_breaches_id"), table_name="breaches")
    op.drop_table("breaches")

    op.drop_index(op.f("ix_positions_industry"), table_name="positions")
    op.drop_index(op.f("ix_positions_name"), table_name="positions")
    op.drop_index(op.f("ix_positions_id"), table_name="positions")
    op.drop_table("positions")

    op.drop_index(op.f("ix_deals_industry"), table_name="deals")
    op.drop_index(op.f("ix_deals_name"), table_name="deals")
    op.drop_index(op.f("ix_deals_id"), table_name="deals")
    op.drop_table("deals")

    op.drop_index(op.f("ix_client_financials_month"), table_name="client_financials")
    op.drop_index(
        op.f("ix_client_financials_client_id"),
        table_name="client_financials",
    )
    op.drop_index(op.f("ix_client_financials_id"), table_name="client_financials")
    op.drop_table("client_financials")

    op.drop_index(op.f("ix_clients_industry"), table_name="clients")
    op.drop_index(op.f("ix_clients_name"), table_name="clients")
    op.drop_index(op.f("ix_clients_id"), table_name="clients")
    op.drop_table("clients")
