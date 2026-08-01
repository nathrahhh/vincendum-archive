"""Baseline for existing production schema.

Revision ID: 0001_baseline_existing_schema
Revises:
Create Date: 2026-08-01

This revision represents the schema already present in production:

- clients
- client_financials
- deals
- positions
- breaches

IMPORTANT:
- upgrade() and downgrade() are intentionally empty (no-op).
- Do NOT use this migration to recreate existing production tables.
- On an existing production database, mark this revision as applied with:

      alembic stamp 0001_baseline_existing_schema

  That records Alembic's version without running DDL.
- Do NOT run ``alembic upgrade head`` on production until you have reviewed
  later incremental migrations. Running stamp (not upgrade) is the safe
  baseline step for databases that already have these tables.
- New empty environments can still use ``Base.metadata.create_all()`` via
  ``init_db()``, then ``alembic stamp head`` so Alembic and the DB agree.
"""

from __future__ import annotations

from typing import Sequence, Union

revision: str = "0001_baseline_existing_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op baseline: production tables already exist.
    pass


def downgrade() -> None:
    # No-op baseline: do not drop production tables.
    pass
