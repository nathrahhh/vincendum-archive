from collections.abc import Generator
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.services.breaches.financial_inputs import get_financial_breach_inputs


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
            ClientORM.__table__,
            DealORM.__table__,
            ClientFinancialORM.__table__,
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
                ClientFinancialORM.__table__,
                DealORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed_client_and_deals(db: Session) -> None:
    db.add(LenderORM(id=1, name="Lender A"))
    db.add(
        ClientORM(
            id=2,
            name="Client Two",
            industry="tech",
            credit_limit=100_000.0,
            lender_id=1,
        )
    )
    db.add(
        DealORM(
            id=10,
            client_id=2,
            name="Approved Deal",
            value=10_000_000,
            status="APPROVED",
        )
    )
    db.commit()


def _financial(
    *,
    financial_id: int,
    month: date,
    gross_profit: float,
    status: str,
) -> ClientFinancialORM:
    return ClientFinancialORM(
        id=financial_id,
        client_id=2,
        month=month,
        revenue=gross_profit * 2,
        cogs=gross_profit,
        gross_profit=gross_profit,
        opex=0.0,
        cash_balance=0.0,
        status=status,
    )


def test_uses_latest_approved_financial_by_month(db_session: Session):
    _seed_client_and_deals(db_session)
    db_session.add_all(
        [
            _financial(
                financial_id=100,
                month=date(2027, 4, 1),
                gross_profit=3_373_121.0,
                status="APPROVED",
            ),
            _financial(
                financial_id=101,
                month=date(2027, 3, 1),
                gross_profit=500.0,
                status="APPROVED",
            ),
        ]
    )
    db_session.commit()

    inputs = get_financial_breach_inputs(
        db_session,
        lender_id=1,
        client_id=2,
    )

    assert inputs.gross_profit == 3_373_121.0
    assert inputs.has_approved_financial is True
    assert inputs.total_deal_value == 10_000_000
    assert inputs.has_approved_deals is True


def test_pending_financial_is_not_used(db_session: Session):
    _seed_client_and_deals(db_session)
    db_session.add(
        _financial(
            financial_id=102,
            month=date(2027, 5, 1),
            gross_profit=500.0,
            status="PENDING",
        )
    )
    db_session.commit()

    inputs = get_financial_breach_inputs(
        db_session,
        lender_id=1,
        client_id=2,
    )

    assert inputs.gross_profit is None
    assert inputs.has_approved_financial is False


def test_no_approved_deals_preserves_missing_deal_behavior(db_session: Session):
    db_session.add(LenderORM(id=1, name="Lender A"))
    db_session.add(
        ClientORM(
            id=2,
            name="Client Two",
            industry="tech",
            credit_limit=100_000.0,
            lender_id=1,
        )
    )
    db_session.add(
        _financial(
            financial_id=103,
            month=date(2027, 1, 1),
            gross_profit=120_000.0,
            status="APPROVED",
        )
    )
    db_session.commit()

    inputs = get_financial_breach_inputs(
        db_session,
        lender_id=1,
        client_id=2,
    )

    assert inputs.has_approved_deals is False
    assert inputs.total_deal_value == 0.0
    assert inputs.gross_profit == 120_000.0
    assert inputs.has_approved_financial is True


def test_wrong_lender_raises_not_found(db_session: Session):
    _seed_client_and_deals(db_session)

    with pytest.raises(HTTPException) as exc_info:
        get_financial_breach_inputs(
            db_session,
            lender_id=999,
            client_id=2,
        )

    assert exc_info.value.status_code == 404
