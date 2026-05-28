from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.position import PositionORM
from app.models.schemas import DealRequest

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/evaluate")
def evaluate_deal(
    deal: DealRequest,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """
    Insert a proposed deal as a new position and return its ID.
    """
    position = PositionORM(
        name=deal.name,
        value=deal.value,
        industry=deal.industry,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return {"id": position.id}
