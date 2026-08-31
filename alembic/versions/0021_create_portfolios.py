"""create_portfolios_and_link_positions

Revision ID: 0021_create_portfolios
Revises: 0020_create_bank_transactions
Create Date: 2026-08-29

Creates portfolios owned by lenders, links positions via portfolio_id,
and removes positions.industry (industry lives on clients).

Existing Position rows are backfilled before portfolio_id becomes NOT NULL:
1. One default portfolio is created per lender.
2. Positions with a client (and lender) are assigned via clients.lender_id.
3. Remaining orphan positions (null client_id / null lender_id) are assigned
   to the lowest-id lender's default portfolio when at least one lender exists.
4. If positions remain unassigned and no lenders exist, the migration aborts.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_create_portfolios"
down_revision: Union[str, None] = "0020_create_bank_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("lender_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_portfolios_lender_id_lenders",
        ),
    )
    op.create_index(
        op.f("ix_portfolios_id"),
        "portfolios",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolios_name"),
        "portfolios",
        ["name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolios_lender_id"),
        "portfolios",
        ["lender_id"],
        unique=False,
    )

    op.add_column(
        "positions",
        sa.Column("portfolio_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_positions_portfolio_id"),
        "positions",
        ["portfolio_id"],
        unique=False,
    )

    conn = op.get_bind()

    # Create one default portfolio per lender for backfill.
    conn.execute(
        sa.text(
            """
            INSERT INTO portfolios (name, lender_id)
            SELECT 'Default Portfolio', l.id
            FROM lenders l
            WHERE NOT EXISTS (
                SELECT 1
                FROM portfolios p
                WHERE p.lender_id = l.id
                  AND p.name = 'Default Portfolio'
            )
            """
        )
    )

    # Assign positions that can be scoped through their client lender.
    conn.execute(
        sa.text(
            """
            UPDATE positions AS pos
            SET portfolio_id = p.id
            FROM clients AS c
            JOIN portfolios AS p
              ON p.lender_id = c.lender_id
             AND p.name = 'Default Portfolio'
            WHERE pos.client_id = c.id
              AND c.lender_id IS NOT NULL
              AND pos.portfolio_id IS NULL
            """
        )
    )

    # Seed / orphan positions without a client lender: attach to first lender
    # default portfolio when one exists.
    remaining = conn.execute(
        sa.text("SELECT COUNT(*) FROM positions WHERE portfolio_id IS NULL")
    ).scalar_one()
    if remaining:
        fallback_portfolio_id = conn.execute(
            sa.text(
                """
                SELECT p.id
                FROM portfolios p
                JOIN lenders l ON l.id = p.lender_id
                WHERE p.name = 'Default Portfolio'
                ORDER BY l.id ASC, p.id ASC
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
        if fallback_portfolio_id is None:
            raise RuntimeError(
                "Cannot make positions.portfolio_id NOT NULL: "
                f"{remaining} position(s) have no portfolio assignment and "
                "no lenders/portfolios exist to receive them."
            )
        conn.execute(
            sa.text(
                """
                UPDATE positions
                SET portfolio_id = :portfolio_id
                WHERE portfolio_id IS NULL
                """
            ),
            {"portfolio_id": fallback_portfolio_id},
        )

    still_null = conn.execute(
        sa.text("SELECT id FROM positions WHERE portfolio_id IS NULL ORDER BY id")
    ).fetchall()
    if still_null:
        ids = ", ".join(str(row[0]) for row in still_null)
        raise RuntimeError(
            "Cannot make positions.portfolio_id NOT NULL: positions still "
            f"missing portfolio_id: {ids}"
        )

    op.alter_column(
        "positions",
        "portfolio_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_positions_portfolio_id_portfolios",
        "positions",
        "portfolios",
        ["portfolio_id"],
        ["id"],
    )

    op.drop_index(op.f("ix_positions_industry"), table_name="positions")
    op.drop_column("positions", "industry")


def downgrade() -> None:
    op.add_column(
        "positions",
        sa.Column("industry", sa.String(length=120), nullable=True),
    )

    conn = op.get_bind()
    # Restore industry from the linked client when available.
    conn.execute(
        sa.text(
            """
            UPDATE positions AS pos
            SET industry = c.industry
            FROM clients AS c
            WHERE pos.client_id = c.id
              AND pos.industry IS NULL
            """
        )
    )
    conn.execute(
        sa.text(
            """
            UPDATE positions
            SET industry = 'Unknown'
            WHERE industry IS NULL
            """
        )
    )

    op.alter_column(
        "positions",
        "industry",
        existing_type=sa.String(length=120),
        nullable=False,
    )
    op.create_index(
        op.f("ix_positions_industry"),
        "positions",
        ["industry"],
        unique=False,
    )

    op.drop_constraint(
        "fk_positions_portfolio_id_portfolios",
        "positions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_positions_portfolio_id"), table_name="positions")
    op.drop_column("positions", "portfolio_id")

    op.drop_index(op.f("ix_portfolios_lender_id"), table_name="portfolios")
    op.drop_index(op.f("ix_portfolios_name"), table_name="portfolios")
    op.drop_index(op.f("ix_portfolios_id"), table_name="portfolios")
    op.drop_table("portfolios")
