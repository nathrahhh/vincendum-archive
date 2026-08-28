from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.deal import DealORM
from app.models.position import PositionORM
from app.models.schemas import DealApprovalRequest, DealRecord, DealRequest, Position, RiskEvaluation
from app.models.user import UserORM
from app.services.client_credit_engine import ClientCreditEngine
from app.services.deal_service import _to_deal_record
from app.services.deal_service import approve_deal as approve_deal_service
from app.services.deal_service import create_deal as create_deal_service
from app.services.deal_service import reject_deal as reject_deal_service
from app.services.concentration_risk_engine import RiskEngine

router = APIRouter()
deals_router = APIRouter(prefix="/deals", tags=["deals"])
clients_deals_router = APIRouter(prefix="/clients", tags=["deals"])
client_me_router = APIRouter(prefix="/client", tags=["client"])


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


@deals_router.get("", response_model=list[DealRecord])
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
    return [_to_deal_record(deal) for deal in rows]


@clients_deals_router.get("/{client_id}/deals", response_model=list[DealRecord])
def list_client_deals(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> list[DealRecord]:
    """Return deals for a client owned by the authenticated admin's lender."""
    lender_id = get_user_lender_id(current_user)
    client = db.execute(
        select(ClientORM).where(
            ClientORM.id == client_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")

    rows = db.execute(
        select(DealORM)
        .where(DealORM.client_id == client_id)
        .order_by(DealORM.id.desc())
    ).scalars().all()
    return [_to_deal_record(deal) for deal in rows]


@deals_router.post("/evaluate", response_model=RiskEvaluation)
def evaluate_deal(
    deal: DealRequest,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> RiskEvaluation:
    """
    Evaluate a proposed deal using RiskEngine and persist audit records.

    Ownership and industry come from the authenticated client profile.
    """
    existing_positions = db.execute(select(PositionORM).order_by(PositionORM.name)).scalars().all()
    portfolio = [Position(name=p.name, value=p.value, industry=p.industry) for p in existing_positions]
    risk_deal = SimpleNamespace(
        name=deal.name,
        value=deal.value,
        industry=current_client.industry,
    )
    risk_engine = RiskEngine()
    result = risk_engine.evaluate_deal(portfolio=portfolio, deal=risk_deal)
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
        term_months=deal.term_months,
        status=deal_status,
    )
    db.add(logged_deal)
    db.commit()
    db.refresh(logged_deal)

    return result


@deals_router.post("/{deal_id}/approve", response_model=DealRecord)
def approve_deal(
    deal_id: int,
    payload: DealApprovalRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> DealRecord:
    """Approve a pending deal and add it to the portfolio."""
    lender_id = get_user_lender_id(current_user)
    deal = _deal_for_lender(db, deal_id, lender_id)
    if deal is None:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    return approve_deal_service(
        db,
        deal_id,
        payload=payload,
        lender_id=lender_id,
        user_id=current_user.id,
    )


@deals_router.post("/{deal_id}/reject", response_model=DealRecord)
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


@client_me_router.get("/me/deals", response_model=list[DealRecord])
def list_my_client_deals(
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> list[DealRecord]:
    rows = db.execute(
        select(DealORM)
        .where(DealORM.client_id == current_client.id)
        .order_by(DealORM.id.desc())
    ).scalars().all()
    return [_to_deal_record(row) for row in rows]


@client_me_router.post("/me/deals", response_model=DealRecord)
def create_my_client_deal(
    payload: DealRequest,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> DealRecord:
    """
    Submit a new PENDING deal for the authenticated client.

    ``client_id`` is taken only from the authenticated client profile.
    """
    return create_deal_service(
        db,
        current_client=current_client,
        payload=payload,
    )


router.include_router(deals_router)
router.include_router(clients_deals_router)
router.include_router(client_me_router)
