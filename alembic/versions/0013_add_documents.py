"""add_documents

Revision ID: 0013_add_documents
Revises: 0012_rewrite_breaches
Create Date: 2026-08-14

Creates the documents table for application- and client-owned document
metadata. Documents are stored in Vincendum-managed S3 or as an external
link. Does not modify existing tables.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013_add_documents"
down_revision: Union[str, None] = "0012_rewrite_breaches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lender_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "storage_type",
            sa.String(length=50),
            nullable=False,
            server_default="s3",
        ),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lender_id"],
            ["lenders.id"],
            name="fk_documents_lender_id_lenders",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["clients.id"],
            name="fk_documents_client_id_clients",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["client_applications.id"],
            name="fk_documents_application_id_client_applications",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "client_id IS NOT NULL OR application_id IS NOT NULL",
            name="ck_documents_client_or_application",
        ),
        sa.CheckConstraint(
            "storage_type IN ('s3', 'external')",
            name="ck_documents_storage_type",
        ),
        sa.CheckConstraint(
            "("
            "storage_type = 's3' "
            "AND storage_key IS NOT NULL "
            "AND external_url IS NULL"
            ") OR ("
            "storage_type = 'external' "
            "AND external_url IS NOT NULL "
            "AND storage_key IS NULL"
            ")",
            name="ck_documents_storage_fields",
        ),
    )
    op.create_index(
        op.f("ix_documents_lender_id"),
        "documents",
        ["lender_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documents_client_id"),
        "documents",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documents_application_id"),
        "documents",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_documents_created_at"),
        "documents",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_documents_created_at"), table_name="documents")
    op.drop_index(op.f("ix_documents_application_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_client_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_lender_id"), table_name="documents")
    op.drop_table("documents")
