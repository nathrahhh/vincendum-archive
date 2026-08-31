"""Tests for deal approval generating a repayment schedule."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models.audit_log import AuditLogORM
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.lender import LenderORM
from app.models.position import PositionORM
from app.models.repayment import RepaymentORM
from app.models.user import UserORM
from app.models.schemas import DealApprovalRequest
from app.services.deal_service import approve_deal


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
    Base.metadata.create_all(
        bind=engine,
        tables=[
            LenderORM.__table__,
            ClientORM.__table__,
            UserORM.__table__,
            DealORM.__table__,
            PositionORM.__table__,
            RepaymentORM.__table__,
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
                RepaymentORM.__table__,
                PositionORM.__table__,
                DealORM.__table__,
                UserORM.__table__,
                ClientORM.__table__,
                LenderORM.__table__,
            ],
        )


def _seed(db: Session) -> None:
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
        UserORM(
            id=8,
            email="admin@example.com",
            auth0_user_id="auth0|admin",
            role="admin",
            lender_id=1,
            client_id=None,
        )
    )
    db.commit()


def _pending_deal(**overrides: object) -> DealORM:
    values: dict[str, object] = {
        "id": 10,
        "client_id": 2,
        "name": "Term Loan A",
        "value": 100_000.0,
        "status": "PENDING",
        "principal_amount": 100_000.0,
        "interest_rate": 7.0,
        "interest_rate_type": "fixed",
        "repayment_method": "amortizing",
        "term_months": 12,
        "payment_frequency": "monthly",
        "first_payment_date": date(2026, 2, 1),
    }
    values.update(overrides)
    return DealORM(**values)  # type: ignore[arg-type]


def _approval_payload(**overrides: object) -> DealApprovalRequest:
    values: dict[str, object] = {
        "principal_amount": 100_000.0,
        "interest_rate": 7.0,
        "interest_rate_type": "fixed",
        "repayment_method": "amortizing",
        "term_months": 12,
        "start_date": date(2026, 1, 15),
        "payment_frequency": "monthly",
        "first_payment_date": date(2026, 2, 1),
        "maturity_date": None,
    }
    values.update(overrides)
    return DealApprovalRequest(**values)  # type: ignore[arg-type]


def _repayment_count(db: Session, deal_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(RepaymentORM).where(
            RepaymentORM.deal_id == deal_id
        )
    ).scalar_one()


def _position_count(db: Session) -> int:
    return db.execute(select(func.count()).select_from(PositionORM)).scalar_one()


def test_approve_valid_deal_creates_schedule_and_position(db_session: Session) -> None:
    _seed(db_session)
    db_session.add(_pending_deal(term_months=12))
    db_session.commit()

    record = approve_deal(
        db_session,
        10,
        payload=_approval_payload(term_months=12),
        lender_id=1,
        user_id=8,
    )

    assert record.status == "APPROVED"
    deal = db_session.get(DealORM, 10)
    assert deal is not None
    assert deal.status == "APPROVED"

    assert _position_count(db_session) == 1
    position = db_session.execute(select(PositionORM)).scalar_one()
    assert position.deal_id == 10
    assert position.value == 100_000.0

    repayments = db_session.execute(
        select(RepaymentORM).where(RepaymentORM.deal_id == 10)
    ).scalars().all()
    assert len(repayments) == 12
    for row in repayments:
        assert row.deal_id == 10
        assert row.status == "SCHEDULED"
        assert row.principal_paid == 0
        assert row.interest_paid == 0
        assert row.total_paid == 0


def test_approve_missing_terms_keeps_deal_pending(db_session: Session) -> None:
    _seed(db_session)
    db_session.add(_pending_deal(principal_amount=None))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        approve_deal(
            db_session,
            10,
            payload=_approval_payload(payment_frequency="quarterly"),
            lender_id=1,
            user_id=8,
        )

    assert exc_info.value.status_code == 400
    db_session.rollback()

    deal = db_session.get(DealORM, 10)
    assert deal is not None
    assert deal.status == "PENDING"
    assert _repayment_count(db_session, 10) == 0
    assert _position_count(db_session) == 0


def test_approve_unsupported_configuration_keeps_deal_pending(
    db_session: Session,
) -> None:
    _seed(db_session)
    db_session.add(_pending_deal(repayment_method="interest_only"))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        approve_deal(
            db_session,
            10,
            payload=_approval_payload(repayment_method="interest_only"),
            lender_id=1,
            user_id=8,
        )

    assert exc_info.value.status_code == 400
    db_session.rollback()

    deal = db_session.get(DealORM, 10)
    assert deal is not None
    assert deal.status == "PENDING"
    assert _repayment_count(db_session, 10) == 0
    assert _position_count(db_session) == 0


def test_non_pending_deal_cannot_be_approved(db_session: Session) -> None:
    _seed(db_session)
    db_session.add(_pending_deal(status="APPROVED"))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        approve_deal(
            db_session,
            10,
            payload=_approval_payload(),
            lender_id=1,
            user_id=8,
        )

    assert exc_info.value.status_code == 400
    assert "not pending" in exc_info.value.detail
    assert _repayment_count(db_session, 10) == 0
    assert _position_count(db_session) == 0


def test_approve_records_audit_log(db_session: Session) -> None:
    _seed(db_session)
    db_session.add(_pending_deal(term_months=3))
    db_session.commit()

    approve_deal(
        db_session,
        10,
        payload=_approval_payload(term_months=3),
        lender_id=1,
        user_id=8,
    )

    audit = db_session.execute(
        select(AuditLogORM).where(
            AuditLogORM.action == "deal.approved",
            AuditLogORM.resource_type == "deal",
            AuditLogORM.resource_id == 10,
        )
    ).scalar_one()
    assert audit.lender_id == 1
    assert audit.user_id == 8
