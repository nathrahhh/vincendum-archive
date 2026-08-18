from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db import Base, get_db
from app.main import app
from app.models.lender import LenderORM
from app.models.user import UserORM


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            UserORM.__table__,
        ],
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                UserORM.__table__,
                LenderORM.__table__,
            ],
        )


def _admin_user(*, user_id: int = 1, lender_id: int | None = None) -> UserORM:
    return UserORM(
        id=user_id,
        email=f"admin{user_id}@example.com",
        auth0_user_id=f"auth0|admin{user_id}",
        role="admin",
        lender_id=lender_id,
    )


def _override(user: UserORM, db: Session) -> TestClient:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def _clear_overrides() -> None:
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def test_onboard_creates_lender_with_persisted_slug(db_session: Session):
    user = _admin_user()
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    client = _override(user, db_session)
    try:
        response = client.post("/lenders/onboard", json={"name": "Acme Capital"})
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Acme Capital"
    assert payload["slug"] == "acme-capital"

    stored = db_session.execute(
        select(LenderORM).where(LenderORM.id == payload["id"])
    ).scalar_one()
    assert stored.name == "Acme Capital"
    assert stored.slug == "acme-capital"
    db_session.refresh(user)
    assert user.lender_id == stored.id


def test_onboard_allocates_unique_slug_when_name_collides(db_session: Session):
    first_user = _admin_user(user_id=1)
    second_user = _admin_user(user_id=2)
    db_session.add_all([first_user, second_user])
    db_session.commit()
    db_session.refresh(first_user)
    db_session.refresh(second_user)

    client = _override(first_user, db_session)
    try:
        first = client.post("/lenders/onboard", json={"name": "Acme Capital"})
    finally:
        _clear_overrides()

    assert first.status_code == 200
    assert first.json()["slug"] == "acme-capital"

    client = _override(second_user, db_session)
    try:
        second = client.post("/lenders/onboard", json={"name": "Acme Capital"})
    finally:
        _clear_overrides()

    assert second.status_code == 200
    assert second.json()["slug"] == "acme-capital-2"

    slugs = db_session.execute(select(LenderORM.slug).order_by(LenderORM.id)).scalars().all()
    assert slugs == ["acme-capital", "acme-capital-2"]


def test_duplicate_lender_slug_is_rejected(db_session: Session):
    db_session.add(LenderORM(name="Lender A", slug="lender-a"))
    db_session.commit()

    db_session.add(LenderORM(name="Lender A Copy", slug="lender-a"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    stored = db_session.execute(select(LenderORM)).scalars().all()
    assert len(stored) == 1
    assert stored[0].slug == "lender-a"
