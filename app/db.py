import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
)


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import ORM models so they register on Base.metadata before create_all.
    # Prefer Alembic migrations for schema changes; create_all is a local fallback.
    from app.models.breach import BreachORM  # noqa: F401
    from app.models.client import ClientORM  # noqa: F401
    from app.models.client_application import ClientApplicationORM  # noqa: F401
    from app.models.client_financial import ClientFinancialORM  # noqa: F401
    from app.models.client_invitation import ClientInvitationORM  # noqa: F401
    from app.models.deal import DealORM  # noqa: F401
    from app.models.lender import LenderORM  # noqa: F401
    from app.models.position import PositionORM  # noqa: F401
    from app.models.user import UserORM  # noqa: F401

    Base.metadata.create_all(bind=engine)
