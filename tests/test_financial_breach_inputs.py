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
from app.models.repayment import RepaymentORM
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
            RepaymentORM.__table__,
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
                RepaymentORM.__table__,
                DealORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed_client_and_deal(db: Session) -> None:
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


def _repayment(
    *,
    repayment_id: int,
    deal_id: int,
    due_date: date,
    total_due: float,
) -> RepaymentORM:
    return RepaymentORM(
        id=repayment_id,
        deal_id=deal_id,
        due_date=due_date,
        principal_due=total_due * 0.8,
        interest_due=total_due * 0.2,
        total_due=total_due,
        status="SCHEDULED",
    )


def test_uses_latest_approved_financial_by_month(db_session: Session):
    _seed_client_and_deal(db_session)
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
            _repayment(
                repayment_id=1,
                deal_id=10,
                due_date=date(2027, 4, 15),
                total_due=5_000.0,
            ),
            _repayment(
                repayment_id=2,
                deal_id=10,
                due_date=date(2027, 3, 15),
                total_due=99_000.0,
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
    assert inputs.period_start == date(2027, 4, 1)
    assert inputs.period_end == date(2027, 4, 30)
    assert inputs.scheduled_debt_service == 5_000.0
    assert inputs.has_scheduled_debt_service is True


def test_pending_financial_is_not_used(db_session: Session):
    _seed_client_and_deal(db_session)
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
    assert inputs.period_start is None
    assert inputs.period_end is None
    assert inputs.scheduled_debt_service == 0.0
    assert inputs.has_scheduled_debt_service is False


def test_no_in_period_repayments_preserves_missing_debt_service(
    db_session: Session,
) -> None:
    db_session.add(LenderORM(id=1, name="Lender A", slug="lender-a", capital_base=10_000_000))
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

    assert inputs.has_scheduled_debt_service is False
    assert inputs.scheduled_debt_service == 0.0
    assert inputs.gross_profit == 120_000.0
    assert inputs.has_approved_financial is True
    assert inputs.period_start == date(2027, 1, 1)
    assert inputs.period_end == date(2027, 1, 31)


def test_explicit_period_overrides_financial_month(db_session: Session) -> None:
    _seed_client_and_deal(db_session)
    db_session.add_all(
        [
            _financial(
                financial_id=104,
                month=date(2027, 4, 1),
                gross_profit=10_000.0,
                status="APPROVED",
            ),
            _repayment(
                repayment_id=3,
                deal_id=10,
                due_date=date(2027, 4, 10),
                total_due=1_000.0,
            ),
            _repayment(
                repayment_id=4,
                deal_id=10,
                due_date=date(2027, 6, 10),
                total_due=2_500.0,
            ),
        ]
    )
    db_session.commit()

    inputs = get_financial_breach_inputs(
        db_session,
        lender_id=1,
        client_id=2,
        period_start=date(2027, 6, 1),
        period_end=date(2027, 6, 30),
    )

    assert inputs.gross_profit == 10_000.0
    assert inputs.period_start == date(2027, 6, 1)
    assert inputs.period_end == date(2027, 6, 30)
    assert inputs.scheduled_debt_service == 2_500.0
    assert inputs.has_scheduled_debt_service is True


def test_excludes_non_approved_deal_repayments(db_session: Session) -> None:
    _seed_client_and_deal(db_session)
    db_session.add(
        DealORM(
            id=11,
            client_id=2,
            name="Pending Deal",
            value=1_000_000,
            status="PENDING",
        )
    )
    db_session.add_all(
        [
            _financial(
                financial_id=105,
                month=date(2027, 4, 1),
                gross_profit=10_000.0,
                status="APPROVED",
            ),
            _repayment(
                repayment_id=5,
                deal_id=11,
                due_date=date(2027, 4, 12),
                total_due=9_999.0,
            ),
        ]
    )
    db_session.commit()

    inputs = get_financial_breach_inputs(
        db_session,
        lender_id=1,
        client_id=2,
    )

    assert inputs.scheduled_debt_service == 0.0
    assert inputs.has_scheduled_debt_service is False


def test_wrong_lender_raises_not_found(db_session: Session):
    _seed_client_and_deal(db_session)

    with pytest.raises(HTTPException) as exc_info:
        get_financial_breach_inputs(
            db_session,
            lender_id=999,
            client_id=2,
        )

    assert exc_info.value.status_code == 404
