from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import PositionORM
from app.models.schemas import Position


def get_portfolio(db: Session) -> list[Position]:
    rows = db.execute(select(PositionORM).order_by(PositionORM.name)).scalars().all()
    return [Position(name=r.name, value=r.value, industry=r.industry) for r in rows]


def create_position(db: Session, position: Position) -> Position:
    row = PositionORM(name=position.name, value=position.value, industry=position.industry)
    db.add(row)
    db.commit()
    db.refresh(row)
    return Position(name=row.name, value=row.value, industry=row.industry)


def get_position_by_name(db: Session, name: str) -> Position | None:
    row = db.execute(select(PositionORM).where(PositionORM.name == name)).scalar_one_or_none()
    if row is None:
        return None
    return Position(name=row.name, value=row.value, industry=row.industry)


def update_position(db: Session, name: str, position: Position) -> Position | None:
    row = db.execute(select(PositionORM).where(PositionORM.name == name)).scalar_one_or_none()
    if row is None:
        return None
    row.name = position.name
    row.value = position.value
    row.industry = position.industry
    db.commit()
    db.refresh(row)
    return Position(name=row.name, value=row.value, industry=row.industry)


def delete_position(db: Session, name: str) -> bool:
    row = db.execute(select(PositionORM).where(PositionORM.name == name)).scalar_one_or_none()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def seed_portfolio_if_empty(db: Session) -> None:
    existing = db.execute(select(PositionORM.id).limit(1)).first()
    if existing is not None:
        return

    seed_data = [
        PositionORM(name="Alpha Manufacturing Loan", value=2_500_000, industry="Manufacturing"),
        PositionORM(name="Beta Retail Loan", value=1_800_000, industry="Retail"),
        PositionORM(name="Gamma Tech Loan", value=3_200_000, industry="Technology"),
        PositionORM(name="Delta Healthcare Loan", value=2_100_000, industry="Healthcare"),
        PositionORM(name="Epsilon Energy Loan", value=1_500_000, industry="Energy"),
    ]
    db.add_all(seed_data)
    db.commit()
