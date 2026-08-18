"""add_lender_slug

Revision ID: 0015_add_lender_slug
Revises: 0014_clientappupdates
Create Date: 2026-08-16

Adds lenders.slug (unique, NOT NULL) for public application URLs such as
/apply/acme-capital.

Existing rows are backfilled from lenders.name as lowercase URL-safe
slugs. Duplicate base slugs receive a deterministic ``-{id}`` suffix.
"""

from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0015_add_lender_slug"
down_revision: Union[str, None] = "0014_clientappupdates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _slugify(name: str) -> str:
    """Convert a lender name into a lowercase URL-safe slug."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def upgrade() -> None:
    op.add_column(
        "lenders",
        sa.Column("slug", sa.String(length=255), nullable=True),
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, name FROM lenders ORDER BY id")
    ).fetchall()

    used_slugs: set[str] = set()
    for lender_id, name in rows:
        base = _slugify(name or "")
        if not base:
            base = f"lender-{lender_id}"

        slug = base
        if slug in used_slugs:
            # Deterministic unique suffix from the primary key.
            slug = f"{base}-{lender_id}"

        # Extremely defensive: if ``base-{id}`` somehow collided, keep
        # appending the id until unique (should not happen in practice).
        while slug in used_slugs:
            slug = f"{slug}-{lender_id}"

        used_slugs.add(slug)
        conn.execute(
            sa.text("UPDATE lenders SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": lender_id},
        )

    remaining_nulls = conn.execute(
        sa.text("SELECT id FROM lenders WHERE slug IS NULL ORDER BY id")
    ).fetchall()
    if remaining_nulls:
        ids = ", ".join(str(row[0]) for row in remaining_nulls)
        raise RuntimeError(
            "Cannot make lenders.slug NOT NULL: rows still have NULL slug "
            f"(ids: {ids})."
        )

    op.alter_column(
        "lenders",
        "slug",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.create_index(
        op.f("ix_lenders_slug"),
        "lenders",
        ["slug"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_lenders_slug"), table_name="lenders")
    op.drop_column("lenders", "slug")
