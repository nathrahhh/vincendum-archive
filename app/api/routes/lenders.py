from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.lender import LenderORM
from app.models.schemas import LenderOnboardRequest, LenderResponse
from app.models.user import UserORM

router = APIRouter(prefix="/lenders", tags=["lenders"])


@router.post("/onboard", response_model=LenderResponse)
def onboard_lender(
    payload: LenderOnboardRequest,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
) -> LenderResponse:
    """
    Create a lender for a first-time admin and assign ``users.lender_id``.
    """
    if current_user.lender_id is not None:
        raise HTTPException(
            status_code=400,
            detail="User has already completed lender onboarding",
        )

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Lender name is required")

    lender = LenderORM(name=name)
    db.add(lender)
    db.flush()

    current_user.lender_id = lender.id
    db.commit()
    db.refresh(lender)

    return LenderResponse(id=lender.id, name=lender.name)
