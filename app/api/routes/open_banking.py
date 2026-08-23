"""Open Banking API routes (client bank connection foundation)."""

from __future__ import annotations

import logging
import os
import secrets
from collections.abc import Generator
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
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
from app.models.bank_account import BankAccountORM
from app.models.bank_connection import BankConnectionORM
from app.models.bank_transaction import BankTransactionORM
from app.models.client import ClientORM
from app.models.user import UserORM
from app.services.open_banking_service import (
    STATUS_AUTHORIZED,
    STATUS_CANCELLED,
    STATUS_FAILED,
    OpenBankingService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/client", tags=["open-banking"])


class StartConnectionResponse(BaseModel):
    bank_connection_id: int
    truelayer_connection_id: str
    status: str
    authorization_url: str | None


class BankAccountResponse(BaseModel):
    id: int
    bank_connection_id: int
    truelayer_account_id: str
    account_type: str | None
    currency: str | None
    created_at: datetime
    updated_at: datetime


class BankTransactionResponse(BaseModel):
    id: int
    bank_account_id: int
    truelayer_transaction_id: str
    booking_date: datetime | None
    value_date: datetime | None
    amount: Decimal
    currency: str
    description: str | None
    transaction_type: str | None
    created_at: datetime
    updated_at: datetime


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


def _frontend_callback_url() -> str:
    value = os.getenv("OPEN_BANKING_FRONTEND_CALLBACK_URL", "").strip()
    if not value:
        raise HTTPException(
            status_code=503,
            detail="Open Banking frontend callback URL is not configured",
        )
    return value


def _client_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    return request.client.host


def _append_query(url: str, params: dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(params)
    return urlunparse(parsed._replace(query=urlencode(query)))


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
    callback_state = secrets.token_urlsafe(32)
    return_uri = _append_query(_redirect_uri(), {"state": callback_state})

    try:
        data_connection = open_banking.start_connection(
            user_name=current_client.name,
            user_email=current_user.email,
            return_uri=return_uri,
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
        callback_state=callback_state,
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


@router.get(
    "/me/open-banking/accounts",
    response_model=list[BankAccountResponse],
)
def list_open_banking_accounts(
    request: Request,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
    open_banking: OpenBankingService = Depends(get_open_banking_service),
) -> list[BankAccountResponse]:
    """Sync authorised TrueLayer accounts into bank_accounts and return them."""
    connections = list(
        db.execute(
            select(BankConnectionORM).where(
                BankConnectionORM.client_id == current_client.id
            )
        ).scalars().all()
    )

    for connection in connections:
        if connection.status != STATUS_AUTHORIZED:
            continue
        try:
            provider_accounts = open_banking.list_accounts(
                connection.truelayer_connection_id,
                user_ip=_client_ip(request),
            )
        except TrueLayerConfigError:
            raise HTTPException(
                status_code=503,
                detail="Open Banking is not configured",
            ) from None
        except TrueLayerAPIError as exc:
            status_code = (
                exc.status_code if exc.status_code in {400, 401, 403, 404, 429} else 502
            )
            raise HTTPException(
                status_code=status_code,
                detail="Open Banking provider rejected the accounts request",
            ) from None
        except TrueLayerError:
            raise HTTPException(
                status_code=502,
                detail="Open Banking provider error",
            ) from None

        existing_rows = list(
            db.execute(
                select(BankAccountORM).where(
                    BankAccountORM.bank_connection_id == connection.id
                )
            ).scalars().all()
        )
        by_truelayer_id = {
            row.truelayer_account_id: row for row in existing_rows
        }

        for account in provider_accounts:
            account_type = account.account_type or account.type
            existing = by_truelayer_id.get(account.id)
            if existing is None:
                row = BankAccountORM(
                    bank_connection_id=connection.id,
                    truelayer_account_id=account.id,
                    account_type=account_type,
                    currency=account.currency,
                )
                db.add(row)
                by_truelayer_id[account.id] = row
            else:
                existing.account_type = account_type
                existing.currency = account.currency

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist bank accounts for client_id=%s",
            current_client.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to save bank accounts",
        ) from None

    connection_ids = [connection.id for connection in connections]
    if not connection_ids:
        return []

    persisted = list(
        db.execute(
            select(BankAccountORM)
            .where(BankAccountORM.bank_connection_id.in_(connection_ids))
            .order_by(BankAccountORM.id)
        ).scalars().all()
    )
    return [
        BankAccountResponse(
            id=row.id,
            bank_connection_id=row.bank_connection_id,
            truelayer_account_id=row.truelayer_account_id,
            account_type=row.account_type,
            currency=row.currency,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in persisted
    ]


@router.get(
    "/me/open-banking/accounts/{account_id}/transactions",
    response_model=list[BankTransactionResponse],
)
def sync_open_banking_account_transactions(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
    open_banking: OpenBankingService = Depends(get_open_banking_service),
) -> list[BankTransactionResponse]:
    """Sync TrueLayer transactions for a client-owned bank account and return them."""
    account = db.execute(
        select(BankAccountORM)
        .join(BankConnectionORM)
        .where(
            BankAccountORM.id == account_id,
            BankConnectionORM.client_id == current_client.id,
        )
    ).scalar_one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="Bank account not found")

    connection = account.bank_connection
    if connection.status != STATUS_AUTHORIZED:
        raise HTTPException(
            status_code=409,
            detail="Bank connection is not authorised",
        )

    try:
        from_date, to_date = open_banking.default_transaction_date_range()
        provider_transactions = open_banking.fetch_account_transactions(
            connection.truelayer_connection_id,
            account.truelayer_account_id,
            from_date=from_date,
            to_date=to_date,
            user_ip=_client_ip(request),
            poll_interval_seconds=0,
            max_poll_attempts=40,
        )
    except TrueLayerConfigError:
        raise HTTPException(
            status_code=503,
            detail="Open Banking is not configured",
        ) from None
    except TrueLayerAPIError as exc:
        status_code = (
            exc.status_code if exc.status_code in {400, 401, 403, 404, 429} else 502
        )
        raise HTTPException(
            status_code=status_code,
            detail="Open Banking provider rejected the transactions request",
        ) from None
    except TrueLayerError:
        raise HTTPException(
            status_code=502,
            detail="Open Banking provider error",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    existing_rows = list(
        db.execute(
            select(BankTransactionORM).where(
                BankTransactionORM.bank_account_id == account.id
            )
        ).scalars().all()
    )
    by_truelayer_id = {
        row.truelayer_transaction_id: row for row in existing_rows
    }

    for txn in provider_transactions:
        existing = by_truelayer_id.get(txn.truelayer_transaction_id)
        if existing is None:
            row = BankTransactionORM(
                bank_account_id=account.id,
                truelayer_transaction_id=txn.truelayer_transaction_id,
                booking_date=txn.booking_date,
                value_date=txn.value_date,
                amount=txn.amount,
                currency=txn.currency,
                description=txn.description,
                transaction_type=txn.transaction_type,
            )
            db.add(row)
            by_truelayer_id[txn.truelayer_transaction_id] = row
        else:
            existing.booking_date = txn.booking_date
            existing.value_date = txn.value_date
            existing.amount = txn.amount
            existing.currency = txn.currency
            existing.description = txn.description
            existing.transaction_type = txn.transaction_type

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to persist bank transactions bank_account_id=%s client_id=%s",
            account.id,
            current_client.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to save bank transactions",
        ) from None

    persisted = list(
        db.execute(
            select(BankTransactionORM)
            .where(BankTransactionORM.bank_account_id == account.id)
            .order_by(
                BankTransactionORM.booking_date.desc().nullslast(),
                BankTransactionORM.id.desc(),
            )
        ).scalars().all()
    )
    return [
        BankTransactionResponse(
            id=row.id,
            bank_account_id=row.bank_account_id,
            truelayer_transaction_id=row.truelayer_transaction_id,
            booking_date=row.booking_date,
            value_date=row.value_date,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            transaction_type=row.transaction_type,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in persisted
    ]


@router.get("/open-banking/callback")
def open_banking_callback(
    request: Request,
    db: Session = Depends(get_db),
    open_banking: OpenBankingService = Depends(get_open_banking_service),
    state: str | None = None,
    connection_id: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Handle TrueLayer hosted-page return (no Auth0 bearer required).

    TrueLayer Data V3 does not document return_uri query parameters. At connect
    time Vincendum appends its own ``state`` correlator to ``return_uri``. The
    callback locates ``BankConnectionORM`` by that state and/or by
    ``connection_id`` matching ``truelayer_connection_id`` (never by a
    browser-supplied client_id). Authorisation is confirmed via TrueLayerClient
    account access when no provider ``error`` is present.
    """
    # Never log full query strings — they may include codes or other secrets.
    state_value = state.strip() if state else ""
    connection_id_value = connection_id.strip() if connection_id else ""

    if not state_value and not connection_id_value:
        raise HTTPException(
            status_code=400,
            detail="Missing Open Banking callback parameters",
        )

    row: BankConnectionORM | None = None
    if state_value:
        row = db.execute(
            select(BankConnectionORM).where(
                BankConnectionORM.callback_state == state_value
            )
        ).scalar_one_or_none()
    elif connection_id_value:
        row = db.execute(
            select(BankConnectionORM).where(
                BankConnectionORM.truelayer_connection_id == connection_id_value
            )
        ).scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Bank connection not found",
        )

    if connection_id_value and connection_id_value != row.truelayer_connection_id:
        raise HTTPException(
            status_code=400,
            detail="Open Banking callback connection mismatch",
        )

    logger.info(
        "Open Banking callback received bank_connection_id=%s client_id=%s "
        "provider_error_present=%s",
        row.id,
        row.client_id,
        bool(error),
    )

    if error is not None:
        # Provider-denied / cancelled return — do not treat as authorised.
        row.status = STATUS_CANCELLED if error.strip() else STATUS_FAILED
        _commit_connection_status(db, row)
        return _frontend_redirect(success=False, bank_connection_id=row.id)

    try:
        result = open_banking.finalize_connection_authorization(
            row.truelayer_connection_id,
            user_ip=_client_ip(request),
        )
    except TrueLayerConfigError:
        raise HTTPException(
            status_code=503,
            detail="Open Banking is not configured",
        ) from None
    except TrueLayerError:
        logger.exception(
            "Open Banking provider error during callback bank_connection_id=%s",
            row.id,
        )
        raise HTTPException(
            status_code=502,
            detail="Open Banking provider error",
        ) from None

    row.status = result.status
    _commit_connection_status(db, row)
    return _frontend_redirect(
        success=result.authorized,
        bank_connection_id=row.id,
    )


def _commit_connection_status(db: Session, row: BankConnectionORM) -> None:
    try:
        db.commit()
        db.refresh(row)
    except Exception:
        db.rollback()
        logger.exception(
            "Failed to update bank connection status bank_connection_id=%s",
            row.id,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update bank connection",
        ) from None


def _frontend_redirect(*, success: bool, bank_connection_id: int) -> RedirectResponse:
    redirect_to = _append_query(
        _frontend_callback_url(),
        {
            "status": "success" if success else "failure",
            "bank_connection_id": str(bank_connection_id),
        },
    )
    return RedirectResponse(url=redirect_to, status_code=302)
