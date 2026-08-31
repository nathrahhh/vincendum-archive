from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealApprovalRequest, DealRecord, DealRequest
from app.services.audit_service import record_audit_event
from app.services.repayment_service import generate_and_store_schedule


def _get_deal_or_404(db: Session, deal_id: int) -> DealORM:
    deal = db.execute(select(DealORM).where(DealORM.id == deal_id)).scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return deal


def _to_deal_record(deal: DealORM) -> DealRecord:
    return DealRecord(
        id=deal.id,
        client_id=deal.client_id,
        name=deal.name,
        value=deal.value,
        status=deal.status,
        principal_amount=deal.principal_amount,
        interest_rate=deal.interest_rate,
        interest_rate_type=deal.interest_rate_type,
        repayment_method=deal.repayment_method,
        term_months=deal.term_months,
        start_date=deal.start_date,
        maturity_date=deal.maturity_date,
        payment_frequency=deal.payment_frequency,
        first_payment_date=deal.first_payment_date,
    )


def create_deal(
    db: Session,
    *,
    current_client: ClientORM,
    payload: DealRequest,
) -> DealRecord:
    """
    Create a PENDING deal owned by ``current_client``.

    Ownership comes only from the authenticated client profile.
    Client may only set name, value, and term_months;
    lender repayment terms remain unset until approval.
    """
    deal = DealORM(
        client_id=current_client.id,
        name=payload.name.strip(),
        value=payload.value,
        term_months=payload.term_months,
        status="PENDING",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return _to_deal_record(deal)


def approve_deal(
    db: Session,
    deal_id: int,
    *,
    payload: DealApprovalRequest,
    lender_id: int,
    user_id: int,
) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    # Assign lender-confirmed terms before generating the repayment schedule.
    deal.principal_amount = payload.principal_amount
    deal.interest_rate = payload.interest_rate
    deal.interest_rate_type = payload.interest_rate_type
    deal.repayment_method = payload.repayment_method
    deal.term_months = payload.term_months
    deal.start_date = payload.start_date
    deal.payment_frequency = payload.payment_frequency
    deal.first_payment_date = payload.first_payment_date
    deal.maturity_date = payload.maturity_date

    # Validate terms and stage repayments in this transaction (no commit yet).
    # Failures raise HTTPException before status/position changes.
    generate_and_store_schedule(db, deal.id, commit=False)

    position = PositionORM(deal_id=deal.id, value=deal.value)
    db.add(position)
    deal.status = "APPROVED"
    record_audit_event(
        db,
        lender_id=lender_id,
        user_id=user_id,
        action="deal.approved",
        resource_type="deal",
        resource_id=deal.id,
    )
    db.commit()
    db.refresh(deal)

    return _to_deal_record(deal)


def reject_deal(db: Session, deal_id: int) -> DealRecord:
    deal = _get_deal_or_404(db, deal_id)
    if deal.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Deal {deal_id} is not pending")

    deal.status = "REJECTED"
    db.commit()
    db.refresh(deal)

    return _to_deal_record(deal)
