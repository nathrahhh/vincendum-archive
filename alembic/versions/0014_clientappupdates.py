"""add_client_application_business_fields

Revision ID: 0014_add_client_application_business_fields
Revises: 0013_add_documents
Create Date: 2026-08-16

Adds optional business-profile fields to client_applications:
registered_business_name, companies_house_number, incorporation_year,
headcount, and revenue_last_fy.

Does not modify industry or any other existing columns.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014_clientappupdates"
down_revision: Union[str, None] = "0013_add_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_applications",
        sa.Column(
            "registered_business_name",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "client_applications",
        sa.Column(
            "companies_house_number",
            sa.String(length=50),
            nullable=True,
        ),
    )
    op.add_column(
        "client_applications",
        sa.Column(
            "incorporation_year",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "client_applications",
        sa.Column(
            "headcount",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "client_applications",
        sa.Column(
            "revenue_last_fy",
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("client_applications", "revenue_last_fy")
    op.drop_column("client_applications", "headcount")
    op.drop_column("client_applications", "incorporation_year")
    op.drop_column("client_applications", "companies_house_number")
    op.drop_column("client_applications", "registered_business_name")
