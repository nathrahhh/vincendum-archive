"""Lender onboarding and public slug resolution routes."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.lender import LenderORM
from app.models.schemas import LenderOnboardRequest, LenderResponse
from app.models.user import UserORM

router = APIRouter(prefix="/lenders", tags=["lenders"])


def _slugify(name: str) -> str:
    """Return a lowercase URL-safe slug derived from ``name``."""
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _allocate_unique_slug(db: Session, name: str) -> str:
    """
    Allocate a unique slug for ``name``.

    Prefer the base slug; on collision use readable suffixes ``-2``, ``-3``, …
    """
    base = _slugify(name) or "lender"
    candidate = base
    suffix = 2
    while True:
        exists = db.execute(
            select(LenderORM.id).where(LenderORM.slug == candidate)
        ).scalar_one_or_none()
        if exists is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def _to_response(lender: LenderORM) -> LenderResponse:
    return LenderResponse(id=lender.id, name=lender.name, slug=lender.slug)


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

    slug = _allocate_unique_slug(db, name)
    lender = LenderORM(name=name, slug=slug)
    db.add(lender)

    try:
        db.flush()
        current_user.lender_id = lender.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not create lender due to a conflict; please retry",
        ) from None

    db.refresh(lender)
    return _to_response(lender)


@router.get("/me", response_model=LenderResponse)
def get_my_lender(
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(get_current_user),
) -> LenderResponse:
    """Return the lender assigned to the authenticated user."""
    if current_user.lender_id is None:
        raise HTTPException(
            status_code=403,
            detail="User is not assigned to a lender",
        )

    lender = db.execute(
        select(LenderORM).where(LenderORM.id == current_user.lender_id)
    ).scalar_one_or_none()
    if lender is None:
        raise HTTPException(status_code=404, detail="Lender not found")
    return _to_response(lender)


@router.get("/public/{slug}", response_model=LenderResponse)
def get_public_lender_by_slug(
    slug: str,
    db: Session = Depends(get_db),
) -> LenderResponse:
    """Resolve a lender by public slug (no authentication)."""
    lender = db.execute(
        select(LenderORM).where(LenderORM.slug == slug)
    ).scalar_one_or_none()
    if lender is None:
        raise HTTPException(
            status_code=404,
            detail=f"Lender with slug '{slug}' not found",
        )
    return _to_response(lender)
