"""Alembic migration environment.

Uses ``app.db.Base.metadata`` and imports every ORM model so Autogenerate
can see the full schema. Database URL comes from ``DATABASE_URL``.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db import DATABASE_URL, Base

# Import all ORM models so they register on Base.metadata.
from app.models.breach import BreachORM  # noqa: F401
from app.models.client import ClientORM  # noqa: F401
from app.models.client_application import ClientApplicationORM  # noqa: F401
from app.models.client_financial import ClientFinancialORM  # noqa: F401
from app.models.client_invitation import ClientInvitationORM  # noqa: F401
from app.models.deal import DealORM  # noqa: F401
from app.models.lender import LenderORM  # noqa: F401
from app.models.position import PositionORM  # noqa: F401
from app.models.user import UserORM  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Configure it in the environment before "
        "running Alembic."
    )

# Escape % for ConfigParser interpolation (passwords may contain %xx encodings).
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script generation only)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
