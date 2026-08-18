from collections.abc import Generator
from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.breach import BreachORM
from app.models.client import ClientORM
from app.models.client_financial import ClientFinancialORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.services.client_financial_service import approve_client_financial


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(_element, _compiler, **_kw) -> str:
    return "JSON"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.models.audit_log import AuditLogORM
    from app.models.user import UserORM

    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            ClientORM.__table__,
            UserORM.__table__,
            DealORM.__table__,
            ClientFinancialORM.__table__,
            BreachORM.__table__,
            AuditLogORM.__table__,
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
                AuditLogORM.__table__,
                BreachORM.__table__,
                ClientFinancialORM.__table__,
                DealORM.__table__,
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed(db: Session) -> None:
    db.add(LenderORM(id=1, name="Lender A", slug="lender-a"))
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
    db.add_all(
        [
            ClientFinancialORM(
                id=100,
                client_id=2,
                month=date(2027, 4, 1),
                revenue=6_746_242.0,
                cogs=3_373_121.0,
                gross_profit=3_373_121.0,
                opex=0.0,
                cash_balance=0.0,
                status="APPROVED",
            ),
            ClientFinancialORM(
                id=101,
                client_id=2,
                month=date(2027, 5, 1),
                revenue=1_000.0,
                cogs=500.0,
                gross_profit=500.0,
                opex=0.0,
                cash_balance=0.0,
                status="PENDING",
            ),
        ]
    )
    db.commit()


def test_approving_breaching_financial_uses_that_financial_not_newer_approved(
    db_session: Session,
):
    _seed(db_session)

    approve_client_financial(
        db_session,
        101,
        lender_id=1,
        user_id=99,
    )

    breaches = db_session.execute(
        select(BreachORM).where(BreachORM.client_id == 2)
    ).scalars().all()

    assert len(breaches) == 1
    breach = breaches[0]
    assert breach.status == "OPEN"
    assert breach.lender_id == 1
    assert breach.client_id == 2
    assert breach.rule == "financial_gross_profit_ratio"
    assert breach.threshold == 1.2
    assert breach.actual_value == pytest.approx(500.0 / (10_000_000 * 0.01))
    assert "Gross profit: 500.0" in breach.detail


def test_approving_passing_financial_does_not_create_breach(db_session: Session):
    _seed(db_session)
    passing = ClientFinancialORM(
        id=102,
        client_id=2,
        month=date(2027, 6, 1),
        revenue=240_000.0,
        cogs=120_000.0,
        gross_profit=120_000.0,
        opex=0.0,
        cash_balance=0.0,
        status="PENDING",
    )
    db_session.add(passing)
    db_session.commit()

    approve_client_financial(
        db_session,
        102,
        lender_id=1,
        user_id=99,
    )

    breaches = db_session.execute(
        select(BreachORM).where(BreachORM.client_id == 2)
    ).scalars().all()
    assert breaches == []


def test_approve_passes_financial_id_to_breach_workflow(db_session: Session):
    _seed(db_session)

    with patch(
        "app.services.client_financial_service.evaluate_and_persist_financial_breach"
    ) as evaluate:
        approve_client_financial(
            db_session,
            101,
            lender_id=1,
            user_id=99,
        )

    evaluate.assert_called_once_with(
        db_session,
        lender_id=1,
        client_id=2,
        financial_id=101,
    )
