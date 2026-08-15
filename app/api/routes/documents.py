"""Client document metadata API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.schemas import DocumentCreate, DocumentRecord
from app.models.user import UserORM
from app.services.document_service import (
    create_client_document,
    create_lender_client_document,
    get_client_documents,
    get_document,
    get_lender_client_documents,
)

router = APIRouter()
clients_documents_router = APIRouter(prefix="/clients", tags=["documents"])
client_me_router = APIRouter(prefix="/client", tags=["client"])


def _client_lender_id(current_client: ClientORM) -> int:
    if current_client.lender_id is None:
        raise HTTPException(
            status_code=403,
            detail="Client is not assigned to a lender",
        )
    return current_client.lender_id


@client_me_router.get("/me/documents", response_model=list[DocumentRecord])
def list_my_client_documents(
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> list[DocumentRecord]:
    """Return documents belonging to the authenticated client."""
    return get_client_documents(
        db,
        lender_id=_client_lender_id(current_client),
        client_id=current_client.id,
    )


@client_me_router.post("/me/documents", response_model=DocumentRecord)
def create_my_client_document(
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> DocumentRecord:
    """
    Create a document for the authenticated client.

    Ownership comes only from the authenticated client profile.
    """
    return create_client_document(
        db,
        current_client=current_client,
        payload=payload,
    )


@client_me_router.get(
    "/me/documents/{document_id}",
    response_model=DocumentRecord,
)
def get_my_client_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_client: ClientORM = Depends(get_current_client),
) -> DocumentRecord:
    """Return one document belonging to the authenticated client."""
    return get_document(
        db,
        document_id,
        lender_id=_client_lender_id(current_client),
        client_id=current_client.id,
    )


@clients_documents_router.get(
    "/{client_id}/documents",
    response_model=list[DocumentRecord],
)
def list_client_documents(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> list[DocumentRecord]:
    """Return documents for a client owned by the authenticated admin's lender."""
    lender_id = get_user_lender_id(current_user)
    return get_lender_client_documents(
        db,
        lender_id=lender_id,
        client_id=client_id,
    )


@clients_documents_router.post(
    "/{client_id}/documents",
    response_model=DocumentRecord,
)
def create_client_document_for_lender(
    client_id: int,
    payload: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> DocumentRecord:
    """
    Create a document for a client belonging to the authenticated lender.

    ``lender_id`` is taken only from the authenticated admin user.
    """
    lender_id = get_user_lender_id(current_user)
    return create_lender_client_document(
        db,
        lender_id=lender_id,
        client_id=client_id,
        payload=payload,
    )


@clients_documents_router.get(
    "/{client_id}/documents/{document_id}",
    response_model=DocumentRecord,
)
def get_client_document_for_lender(
    client_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: UserORM = Depends(require_admin),
    _: UserORM = Depends(require_lender_user),
) -> DocumentRecord:
    """Return one document for a client owned by the authenticated admin's lender."""
    lender_id = get_user_lender_id(current_user)
    return get_document(
        db,
        document_id,
        lender_id=lender_id,
        client_id=client_id,
    )


router.include_router(clients_documents_router)
router.include_router(client_me_router)
