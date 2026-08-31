"""portfolio_position_deal_restructure

Revision ID: 0024_portfolio_position_deal_restructure
Revises: 0023_client_financials_client_fk
Create Date: 2026-08-31

Restructures lender/portfolio/client/deal/position ownership:

- lenders.capital_base
- portfolios.capital_allocation
- clients.portfolio_id (nullable FK)
- positions: drop name/client_id/portfolio_id; add deal_id (unique FK to deals)

Data migration:
- clients.portfolio_id backfilled from positions.portfolio_id where possible
- positions.deal_id backfilled by matching APPROVED deals on client_id+name+value
- Aborts if any position row cannot be mapped to exactly one deal
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_portfolio_restructure"
down_revision: Union[str, None] = "0023_client_financials_client_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Matches the dashboard's historical $10M capital base hint for existing lenders.
_DEFAULT_LENDER_CAPITAL_BASE = 10_000_000.0


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    lender_columns = {col["name"] for col in inspector.get_columns("lenders")}
    if "capital_base" not in lender_columns:
        op.add_column(
            "lenders",
            sa.Column("capital_base", sa.Float(), nullable=True),
        )
        conn.execute(
            sa.text(
                "UPDATE lenders SET capital_base = :default_capital_base "
                "WHERE capital_base IS NULL"
            ),
            {"default_capital_base": _DEFAULT_LENDER_CAPITAL_BASE},
        )
        op.alter_column(
            "lenders",
            "capital_base",
            existing_type=sa.Float(),
            nullable=False,
        )

    portfolio_columns = {col["name"] for col in inspector.get_columns("portfolios")}
    if "capital_allocation" not in portfolio_columns:
        op.add_column(
            "portfolios",
            sa.Column("capital_allocation", sa.Float(), nullable=True),
        )
        conn.execute(
            sa.text(
                "UPDATE portfolios SET capital_allocation = 0.0 "
                "WHERE capital_allocation IS NULL"
            )
        )
        op.alter_column(
            "portfolios",
            "capital_allocation",
            existing_type=sa.Float(),
            nullable=False,
        )

    client_columns = {col["name"] for col in inspector.get_columns("clients")}
    if "portfolio_id" not in client_columns:
        op.add_column(
            "clients",
            sa.Column("portfolio_id", sa.Integer(), nullable=True),
        )
        op.create_index(
            op.f("ix_clients_portfolio_id"),
            "clients",
            ["portfolio_id"],
            unique=False,
        )
        op.create_foreign_key(
            "fk_clients_portfolio_id_portfolios",
            "clients",
            "portfolios",
            ["portfolio_id"],
            ["id"],
        )
    else:
        client_fks = {
            fk["name"]
            for fk in inspector.get_foreign_keys("clients")
        }
        if "fk_clients_portfolio_id_portfolios" not in client_fks:
            op.create_foreign_key(
                "fk_clients_portfolio_id_portfolios",
                "clients",
                "portfolios",
                ["portfolio_id"],
                ["id"],
            )
        client_indexes = {
            idx["name"] for idx in inspector.get_indexes("clients")
        }
        if op.f("ix_clients_portfolio_id") not in client_indexes:
            op.create_index(
                op.f("ix_clients_portfolio_id"),
                "clients",
                ["portfolio_id"],
                unique=False,
            )

    position_columns = {col["name"] for col in inspector.get_columns("positions")}

    if "portfolio_id" in position_columns:
        conn.execute(
            sa.text(
                """
                UPDATE clients AS c
                SET portfolio_id = p.portfolio_id
                FROM positions AS p
                WHERE p.client_id = c.id
                  AND c.portfolio_id IS NULL
                  AND p.portfolio_id IS NOT NULL
                """
            )
        )

    if "deal_id" not in position_columns:
        op.add_column(
            "positions",
            sa.Column("deal_id", sa.Integer(), nullable=True),
        )

    position_columns = {col["name"] for col in sa.inspect(conn).get_columns("positions")}

    if "deal_id" in position_columns:
        ambiguous = conn.execute(
            sa.text(
                """
                SELECT p.id, COUNT(d.id) AS match_count
                FROM positions AS p
                JOIN deals AS d
                  ON d.client_id = p.client_id
                 AND d.name = p.name
                 AND d.value = p.value
                 AND d.status = 'APPROVED'
                WHERE p.deal_id IS NULL
                  AND p.client_id IS NOT NULL
                GROUP BY p.id
                HAVING COUNT(d.id) > 1
                """
            )
        ).fetchall()
        if ambiguous:
            details = ", ".join(
                f"position {row[0]} ({row[1]} matching deals)"
                for row in ambiguous
            )
            raise RuntimeError(
                "Cannot map positions.deal_id: ambiguous APPROVED deal matches "
                f"for {details}. Resolve duplicates before rerunning migration."
            )

        conn.execute(
            sa.text(
                """
                UPDATE positions AS p
                SET deal_id = d.id
                FROM deals AS d
                WHERE p.deal_id IS NULL
                  AND p.client_id IS NOT NULL
                  AND d.client_id = p.client_id
                  AND d.name = p.name
                  AND d.value = p.value
                  AND d.status = 'APPROVED'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM positions AS existing
                      WHERE existing.deal_id = d.id
                  )
                """
            )
        )

        conn.execute(
            sa.text(
                """
                UPDATE positions AS p
                SET deal_id = (
                    SELECT d.id
                    FROM deals AS d
                    WHERE d.name = p.name
                      AND d.value = p.value
                      AND d.status = 'APPROVED'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM positions AS existing
                          WHERE existing.deal_id = d.id
                      )
                    ORDER BY d.id
                    LIMIT 1
                )
                WHERE p.deal_id IS NULL
                  AND p.client_id IS NULL
                  AND (
                      SELECT COUNT(*)
                      FROM deals AS d
                      WHERE d.name = p.name
                        AND d.value = p.value
                        AND d.status = 'APPROVED'
                        AND NOT EXISTS (
                            SELECT 1
                            FROM positions AS existing
                            WHERE existing.deal_id = d.id
                        )
                  ) = 1
                """
            )
        )

        unmapped = conn.execute(
            sa.text(
                "SELECT id FROM positions WHERE deal_id IS NULL ORDER BY id"
            )
        ).fetchall()
        if unmapped:
            ids = ", ".join(str(row[0]) for row in unmapped)
            raise RuntimeError(
                "Cannot make positions.deal_id NOT NULL: position row(s) "
                f"{ids} could not be mapped to an APPROVED deal. Create matching "
                "deals, remove orphan positions, or backfill deal_id manually "
                "before rerunning this migration."
            )

    position_fks = {fk["name"] for fk in sa.inspect(conn).get_foreign_keys("positions")}
    if "fk_positions_client_id_clients" in position_fks:
        op.drop_constraint(
            "fk_positions_client_id_clients",
            "positions",
            type_="foreignkey",
        )
    if "fk_positions_portfolio_id_portfolios" in position_fks:
        op.drop_constraint(
            "fk_positions_portfolio_id_portfolios",
            "positions",
            type_="foreignkey",
        )

    position_columns = {col["name"] for col in sa.inspect(conn).get_columns("positions")}
    position_indexes = {idx["name"] for idx in sa.inspect(conn).get_indexes("positions")}

    if op.f("ix_positions_portfolio_id") in position_indexes:
        op.drop_index(op.f("ix_positions_portfolio_id"), table_name="positions")
    if "portfolio_id" in position_columns:
        op.drop_column("positions", "portfolio_id")
    if "client_id" in position_columns:
        op.drop_column("positions", "client_id")
    if "industry" in position_columns:
        if op.f("ix_positions_industry") in position_indexes:
            op.drop_index(op.f("ix_positions_industry"), table_name="positions")
        op.drop_column("positions", "industry")
    if "name" in position_columns:
        for index_name in list(position_indexes):
            if index_name and "name" in index_name:
                op.drop_index(index_name, table_name="positions")
        op.drop_column("positions", "name")

    op.alter_column(
        "positions",
        "deal_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    position_fks = {fk["name"] for fk in sa.inspect(conn).get_foreign_keys("positions")}
    if "fk_positions_deal_id_deals" not in position_fks:
        op.create_foreign_key(
            "fk_positions_deal_id_deals",
            "positions",
            "deals",
            ["deal_id"],
            ["id"],
        )

    position_indexes = {idx["name"] for idx in sa.inspect(conn).get_indexes("positions")}
    if op.f("ix_positions_deal_id") not in position_indexes:
        op.create_index(
            op.f("ix_positions_deal_id"),
            "positions",
            ["deal_id"],
            unique=True,
        )
    else:
        op.drop_index(op.f("ix_positions_deal_id"), table_name="positions")
        op.create_index(
            op.f("ix_positions_deal_id"),
            "positions",
            ["deal_id"],
            unique=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    position_fks = {fk["name"] for fk in inspector.get_foreign_keys("positions")}
    if "fk_positions_deal_id_deals" in position_fks:
        op.drop_constraint(
            "fk_positions_deal_id_deals",
            "positions",
            type_="foreignkey",
        )

    position_indexes = {idx["name"] for idx in inspector.get_indexes("positions")}
    if op.f("ix_positions_deal_id") in position_indexes:
        op.drop_index(op.f("ix_positions_deal_id"), table_name="positions")

    position_columns = {col["name"] for col in inspector.get_columns("positions")}
    if "deal_id" in position_columns:
        op.drop_column("positions", "deal_id")

    op.add_column(
        "positions",
        sa.Column("name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "positions",
        sa.Column("client_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "positions",
        sa.Column("portfolio_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "positions",
        sa.Column("industry", sa.String(length=120), nullable=True),
    )

    conn.execute(
        sa.text(
            """
            UPDATE positions
            SET name = 'Restored Position ' || id,
                industry = 'Unknown'
            WHERE name IS NULL
            """
        )
    )
    op.alter_column(
        "positions",
        "name",
        existing_type=sa.String(length=255),
        nullable=False,
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

    client_fks = {fk["name"] for fk in sa.inspect(conn).get_foreign_keys("clients")}
    if "fk_clients_portfolio_id_portfolios" in client_fks:
        op.drop_constraint(
            "fk_clients_portfolio_id_portfolios",
            "clients",
            type_="foreignkey",
        )
    client_indexes = {idx["name"] for idx in sa.inspect(conn).get_indexes("clients")}
    if op.f("ix_clients_portfolio_id") in client_indexes:
        op.drop_index(op.f("ix_clients_portfolio_id"), table_name="clients")
    client_columns = {col["name"] for col in sa.inspect(conn).get_columns("clients")}
    if "portfolio_id" in client_columns:
        op.drop_column("clients", "portfolio_id")

    portfolio_columns = {col["name"] for col in sa.inspect(conn).get_columns("portfolios")}
    if "capital_allocation" in portfolio_columns:
        op.drop_column("portfolios", "capital_allocation")

    lender_columns = {col["name"] for col in sa.inspect(conn).get_columns("lenders")}
    if "capital_base" in lender_columns:
        op.drop_column("lenders", "capital_base")
