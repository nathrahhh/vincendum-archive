"""ORM and constraint tests for bank_transactions."""

from __future__ import annotations

import importlib.util
from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.bank_account import BankAccountORM
from app.models.bank_connection import BankConnectionORM
from app.models.bank_transaction import BankTransactionORM
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
            BankTransactionORM.__table__,
        ],
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        class_=Session,
    )
    session = TestingSessionLocal()
    session.execute(text("PRAGMA foreign_keys=ON"))
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(
            bind=engine,
            tables=[
                BankTransactionORM.__table__,
                BankAccountORM.__table__,
                BankConnectionORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed_account(db: Session) -> BankAccountORM:
    db.add(LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000))
    db.add(
        ClientORM(
            id=2,
            name="Client Two",
            industry="tech",
            credit_limit=100_000.0,
            lender_id=1,
        )
    )
    connection = BankConnectionORM(
        id=10,
        client_id=2,
        truelayer_connection_id="tl-conn-1",
        status="authorized",
    )
    db.add(connection)
    db.flush()
    account = BankAccountORM(
        id=20,
        bank_connection_id=connection.id,
        truelayer_account_id="tl-acc-1",
        currency="GBP",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def test_bank_transaction_tablename() -> None:
    assert BankTransactionORM.__tablename__ == "bank_transactions"


def test_bank_transaction_creates_and_relates_to_account(db_session: Session) -> None:
    account = _seed_account(db_session)
    txn = BankTransactionORM(
        bank_account_id=account.id,
        truelayer_transaction_id="tl-txn-1",
        booking_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        amount=Decimal("12.3400"),
        currency="GBP",
        description="Coffee",
        transaction_type="booked",
    )
    db_session.add(txn)
    db_session.commit()
    db_session.refresh(txn)
    db_session.refresh(account)

    assert txn.bank_account_id == account.id
    assert txn.bank_account.id == account.id
    assert txn in account.bank_transactions
    assert txn.amount == Decimal("12.3400")


def test_duplicate_truelayer_transaction_id_on_same_account_rejected(
    db_session: Session,
) -> None:
    account = _seed_account(db_session)
    db_session.add(
        BankTransactionORM(
            bank_account_id=account.id,
            truelayer_transaction_id="tl-txn-dup",
            amount=Decimal("1.00"),
            currency="GBP",
        )
    )
    db_session.commit()

    db_session.add(
        BankTransactionORM(
            bank_account_id=account.id,
            truelayer_transaction_id="tl-txn-dup",
            amount=Decimal("2.00"),
            currency="GBP",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_truelayer_transaction_id_allowed_on_different_accounts(
    db_session: Session,
) -> None:
    account = _seed_account(db_session)
    other = BankAccountORM(
        bank_connection_id=account.bank_connection_id,
        truelayer_account_id="tl-acc-2",
        currency="GBP",
    )
    db_session.add(other)
    db_session.flush()

    db_session.add(
        BankTransactionORM(
            bank_account_id=account.id,
            truelayer_transaction_id="tl-txn-shared",
            amount=Decimal("1.00"),
            currency="GBP",
        )
    )
    db_session.add(
        BankTransactionORM(
            bank_account_id=other.id,
            truelayer_transaction_id="tl-txn-shared",
            amount=Decimal("1.00"),
            currency="GBP",
        )
    )
    db_session.commit()

    rows = db_session.execute(select(BankTransactionORM)).scalars().all()
    assert len(rows) == 2


def test_migration_0020_revision_chain() -> None:
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    path = versions_dir / "0020_create_bank_transactions.py"
    spec = importlib.util.spec_from_file_location("migration_0020", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.revision == "0020_create_bank_transactions"
    assert module.down_revision == "0019_add_callback_state"
    assert callable(module.upgrade)
    assert callable(module.downgrade)
