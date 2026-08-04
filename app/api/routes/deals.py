from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.breach import BreachORM
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealRecord, DealRequest, Position, RiskEvaluation
from app.models.user import UserORM
from app.services.breach_helpers import industry_for_new_breach, reason_for_new_breach
from app.services.client_credit_engine import ClientCreditEngine
from app.services.deal_service import approve_deal as approve_deal_service
from app.services.deal_service import reject_deal as reject_deal_service
from app.services.concentration_risk_engine import RiskEngine

router = APIRouter(prefix="/deals", tags=["deals"])


def _deal_for_lender(
    db: Session,
    deal_id: int,
    lender_id: int,
) -> DealORM | None:
    return db.execute(
        select(DealORM)
        .join(ClientORM, DealORM.client_id == ClientORM.id)
        .where(
            DealORM.id == deal_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()


@router.get("", response_model=list[DealRecord])
def list_deals(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> list[DealRecord]:
    """Return historical evaluated deals for this lender, newest first."""
    lender_id = get_user_lender_id(current_user)
    rows = db.execute(
        select(DealORM)
        .join(ClientORM, DealORM.client_id == ClientORM.id)
        .where(ClientORM.lender_id == lender_id)
        .order_by(DealORM.id.desc())
    ).scalars().all()
    return [
        DealRecord(
            id=row.id,
            client_id=row.client_id,
            name=row.name,
            value=row.value,
            industry=row.industry,
            status=row.status,
        )
        for row in rows
    ]


@router.post("/evaluate", response_model=RiskEvaluation)
def evaluate_deal(
    deal: DealRequest,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> RiskEvaluation:
    """
    Evaluate a proposed deal using RiskEngine and persist audit records.

    Ownership comes from the authenticated client profile, not deal.client_id.
    """
    existing_positions = db.execute(select(PositionORM).order_by(PositionORM.name)).scalars().all()
    portfolio = [Position(name=p.name, value=p.value, industry=p.industry) for p in existing_positions]
    risk_engine = RiskEngine()
    result = risk_engine.evaluate_deal(portfolio=portfolio, deal=deal)
    credit_result = ClientCreditEngine().evaluate_deal(
        db=db,
        client_id=current_client.id,
        deal_value=deal.value,
    )

    concentration_rejected = result.status.value == "REJECTED"
    credit_rejected = not credit_result["approved"]
    deal_status = "REJECTED" if concentration_rejected or credit_rejected else "PENDING"
    logged_deal = DealORM(
     client_id=current_client.id,
     name=deal.name,
     value=deal.value,
     industry=deal.industry,
     status=deal_status,
    )
    db.add(logged_deal)
    db.commit()
    db.refresh(logged_deal)

    if result.breaches:
        # Breaches are stored separately to preserve a normalized risk-event log.
        for breach in result.breaches:
            breach_row = BreachORM(
                reason=reason_for_new_breach(breach),
                industry=industry_for_new_breach(breach, deal.industry),
                rule=breach.rule,
                limit_pct=breach.limit_pct,
                actual_pct=breach.actual_pct,
                detail=breach.detail,
            )
            db.add(breach_row)
        db.commit()

    if credit_rejected:
        breach_row = BreachORM(
            reason="CLIENT_CREDIT_LIMIT_EXCEEDED",
            industry=deal.industry,
            rule="client_credit_limit",
            limit_pct=credit_result["credit_limit"],
            actual_pct=credit_result["current_exposure"] + deal.value,
            detail=(
                f"Current exposure: {credit_result['current_exposure']:,.2f}, "
                f"requested loan amount: {deal.value:,.2f}, "
                f"credit limit: {credit_result['credit_limit']:,.2f}."
            ),
        )
        db.add(breach_row)
        db.commit()

    return result


@router.post("/{deal_id}/approve", response_model=DealRecord)
def approve_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> DealRecord:
    """Approve a pending deal and add it to the portfolio."""
    lender_id = get_user_lender_id(current_user)
    deal = _deal_for_lender(db, deal_id, lender_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return approve_deal_service(db, deal_id)


@router.post("/{deal_id}/reject", response_model=DealRecord)
def reject_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> DealRecord:
    """Reject a pending deal without creating a position."""
    lender_id = get_user_lender_id(current_user)
    deal = _deal_for_lender(db, deal_id, lender_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return reject_deal_service(db, deal_id)
