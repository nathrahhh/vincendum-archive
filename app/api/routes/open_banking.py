"""Open Banking API routes (client bank connection foundation)."""

from __future__ import annotations

import logging
import os
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.integrations.truelayer_client import (
    TrueLayerAPIError,
    TrueLayerClient,
    TrueLayerConfigError,
    TrueLayerError,
)
from app.models.bank_connection import BankConnectionORM
from app.models.client import ClientORM
from app.models.user import UserORM
from app.services.open_banking_service import OpenBankingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client", tags=["open-banking"])


class StartConnectionResponse(BaseModel):
    bank_connection_id: int
    truelayer_connection_id: str
    status: str
    authorization_url: str | None


def get_open_banking_service() -> Generator[OpenBankingService, None, None]:
    client = TrueLayerClient.from_env()
    try:
        yield OpenBankingService(client)
    finally:
        client.close()


def _redirect_uri() -> str:
    value = os.getenv("TRUELAYER_REDIRECT_URI", "").strip()
    if not value:
        raise HTTPException(
            status_code=503,
            detail="Open Banking redirect URI is not configured",
        )
    return value


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


@router.post(
    "/me/open-banking/connect",
    response_model=StartConnectionResponse,
)
def start_open_banking_connection(
    request: Request,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
    current_user: UserORM = Depends(get_current_user),
    open_banking: OpenBankingService = Depends(get_open_banking_service),
) -> StartConnectionResponse:
    """Start TrueLayer bank authorisation for the authenticated client."""
    try:
        data_connection = open_banking.start_connection(
            user_name=current_client.name,
            user_email=current_user.email,
            return_uri=_redirect_uri(),
            user_ip=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except TrueLayerConfigError:
        raise HTTPException(
            status_code=503,
            detail="Open Banking is not configured",
        ) from None
    except TrueLayerAPIError as exc:
        status_code = exc.status_code if exc.status_code in {400, 401, 403, 404, 429} else 502
        raise HTTPException(
            status_code=status_code,
            detail="Open Banking provider rejected the connection request",
        ) from None
    except TrueLayerError:
        raise HTTPException(
            status_code=502,
            detail="Open Banking provider error",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    row = BankConnectionORM(
        client_id=current_client.id,
        truelayer_connection_id=data_connection.id,
        status=data_connection.status,
    )
    db.add(row)
    try:
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist bank connection for client_id=%s",
            current_client.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to save bank connection",
        ) from None

    return StartConnectionResponse(
        bank_connection_id=row.id,
        truelayer_connection_id=row.truelayer_connection_id,
        status=row.status,
        authorization_url=data_connection.hosted_page_uri,
    )
