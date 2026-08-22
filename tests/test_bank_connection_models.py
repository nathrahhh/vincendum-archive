"""ORM and constraint tests for bank_connections / bank_accounts."""

from __future__ import annotations

import importlib.util
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.bank_account import BankAccountORM
from app.models.bank_connection import BankConnectionORM
from app.models.client import ClientORM
from app.models.lender import LenderORM


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            ClientORM.__table__,
            BankConnectionORM.__table__,
            BankAccountORM.__table__,
        ],
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    # Ensure FK enforcement is active on this connection.
    session.execute(text("PRAGMA foreign_keys=ON"))
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                BankAccountORM.__table__,
                BankConnectionORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed_client(db: Session) -> ClientORM:
    db.add(LenderORM(id=1, name="Lender A", slug="lender-a"))
    client = ClientORM(
        id=2,
        name="Client Two",
        industry="tech",
        credit_limit=100_000.0,
        lender_id=1,
    )
    db.add(client)
    db.commit()
    return client


def test_bank_connection_tablename() -> None:
    assert BankConnectionORM.__tablename__ == "bank_connections"


def test_bank_account_tablename() -> None:
    assert BankAccountORM.__tablename__ == "bank_accounts"


def test_bank_connection_belongs_to_client(db_session: Session) -> None:
    client = _seed_client(db_session)
    connection = BankConnectionORM(
        client_id=client.id,
        truelayer_connection_id="tl-conn-1",
        status="authorized",
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)

    assert connection.client_id == client.id
    assert connection.client.id == client.id
    assert connection in client.bank_connections


def test_connection_can_have_multiple_accounts(db_session: Session) -> None:
    client = _seed_client(db_session)
    connection = BankConnectionORM(
        client_id=client.id,
        truelayer_connection_id="tl-conn-1",
        status="authorized",
    )
    db_session.add(connection)
    db_session.flush()

    accounts = [
        BankAccountORM(
            bank_connection_id=connection.id,
            truelayer_account_id="tl-acc-1",
            account_type="current",
            currency="GBP",
        ),
        BankAccountORM(
            bank_connection_id=connection.id,
            truelayer_account_id="tl-acc-2",
            account_type="savings",
            currency="GBP",
        ),
    ]
    db_session.add_all(accounts)
    db_session.commit()
    db_session.refresh(connection)

    assert len(connection.bank_accounts) == 2
    assert {a.truelayer_account_id for a in connection.bank_accounts} == {
        "tl-acc-1",
        "tl-acc-2",
    }


def test_bank_account_belongs_to_one_connection(db_session: Session) -> None:
    client = _seed_client(db_session)
    connection = BankConnectionORM(
        client_id=client.id,
        truelayer_connection_id="tl-conn-1",
        status="authorized",
    )
    db_session.add(connection)
    db_session.flush()

    account = BankAccountORM(
        bank_connection_id=connection.id,
        truelayer_account_id="tl-acc-1",
        currency="GBP",
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    assert account.bank_connection.id == connection.id
    assert account.bank_connection_id == connection.id


def test_duplicate_truelayer_connection_id_rejected(db_session: Session) -> None:
    client = _seed_client(db_session)
    db_session.add(
        BankConnectionORM(
            client_id=client.id,
            truelayer_connection_id="tl-conn-dup",
            status="authorized",
        )
    )
    db_session.commit()

    db_session.add(
        BankConnectionORM(
            client_id=client.id,
            truelayer_connection_id="tl-conn-dup",
            status="authorization_required",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_truelayer_account_id_on_same_connection_rejected(
    db_session: Session,
) -> None:
    client = _seed_client(db_session)
    connection = BankConnectionORM(
        client_id=client.id,
        truelayer_connection_id="tl-conn-1",
        status="authorized",
    )
    db_session.add(connection)
    db_session.flush()

    db_session.add(
        BankAccountORM(
            bank_connection_id=connection.id,
            truelayer_account_id="tl-acc-same",
            currency="GBP",
        )
    )
    db_session.commit()

    db_session.add(
        BankAccountORM(
            bank_connection_id=connection.id,
            truelayer_account_id="tl-acc-same",
            currency="GBP",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_client_required(db_session: Session) -> None:
    db_session.add(
        BankConnectionORM(
            client_id=999,
            truelayer_connection_id="tl-conn-orphan",
            status="authorized",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_migration_revision_chain() -> None:
    path = (
        Path(__file__).resolve().parents[1]
        / "alembic"
        / "versions"
        / "0018_create_bank_connections_and_accounts.py"
    )
    spec = importlib.util.spec_from_file_location("migration_0018", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0018_create_bank_connections_and_accounts"
    assert module.down_revision == "0017_create_repayments"
    assert callable(module.upgrade)
    assert callable(module.downgrade)
