"""Client document metadata API routes."""

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.client import get_current_client
from app.auth.permissions import require_admin
from app.auth.tenant import get_user_lender_id, require_lender_user
from app.db import get_db
from app.models.client import ClientORM
from app.models.lender import LenderORM
from app.models.schemas import DocumentCreate, DocumentRecord
from app.models.user import UserORM
from app.services.documents.document_service import (
    create_application_document,
    create_client_document,
    create_lender_client_document,
    delete_application_document,
    get_application_document,
    get_application_documents,
    get_client_documents,
    get_document,
    get_lender_client_documents,
)
from app.services.documents.storage_service import (
    delete_object,
    generate_download_url,
    generate_upload_url,
)

router = APIRouter()
clients_documents_router = APIRouter(prefix="/clients", tags=["documents"])
client_me_router = APIRouter(prefix="/client", tags=["client"])
apply_documents_router = APIRouter(prefix="/apply", tags=["documents"])


class ApplicationDocumentUploadRequest(BaseModel):
    name: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)


def _client_lender_id(current_client: ClientORM) -> int:
    if current_client.lender_id is None:
        raise HTTPException(
            status_code=403,
            detail="Client is not assigned to a lender",
        )
    return current_client.lender_id


def _lender_id_for_slug(db: Session, lender_slug: str) -> int:
    lender = db.execute(
        select(LenderORM).where(LenderORM.slug == lender_slug)
    ).scalar_one_or_none()
    if lender is None:
        raise HTTPException(
            status_code=404,
            detail=f"Lender with slug '{lender_slug}' not found",
        )
    return lender.id


def _safe_filename(name: str) -> str:
    base = name.strip().replace("\\", "/").split("/")[-1]
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip(".-")
    return base or "file"


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


@apply_documents_router.post(
    "/{lender_slug}/applications/{application_id}/documents/upload-url",
)
def create_public_application_document_upload_url(
    lender_slug: str,
    application_id: int,
    payload: ApplicationDocumentUploadRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create application document metadata and return a presigned S3 upload URL.

    ``lender_id`` comes from ``lender_slug``, not the request body.
    The browser uploads the file directly to S3.
    """
    lender_id = _lender_id_for_slug(db, lender_slug)
    storage_key = (
        f"applications/{application_id}/"
        f"{uuid.uuid4().hex}-{_safe_filename(payload.name)}"
    )
    upload_url = generate_upload_url(
        storage_key,
        payload.content_type.strip(),
    )
    document = create_application_document(
        db,
        lender_id=lender_id,
        application_id=application_id,
        name=payload.name,
        storage_key=storage_key,
        storage_type="s3",
    )
    return {
        "document": document.model_dump(mode="json"),
        "upload_url": upload_url,
    }


@apply_documents_router.get(
    "/{lender_slug}/applications/{application_id}/documents",
    response_model=list[DocumentRecord],
)
def list_public_application_documents(
    lender_slug: str,
    application_id: int,
    db: Session = Depends(get_db),
) -> list[DocumentRecord]:
    """List documents for a public application identified by lender slug."""
    lender_id = _lender_id_for_slug(db, lender_slug)
    return get_application_documents(
        db,
        lender_id=lender_id,
        application_id=application_id,
    )


@apply_documents_router.get(
    "/{lender_slug}/applications/{application_id}/documents/{document_id}",
)
def get_public_application_document(
    lender_slug: str,
    application_id: int,
    document_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Return one application document plus a temporary download URL."""
    lender_id = _lender_id_for_slug(db, lender_slug)
    document = get_application_document(
        db,
        document_id,
        lender_id=lender_id,
        application_id=application_id,
    )
    download_url = None
    if document.storage_type == "s3" and document.storage_key:
        download_url = generate_download_url(document.storage_key)
    return {
        "document": document.model_dump(mode="json"),
        "download_url": download_url,
    }


@apply_documents_router.delete(
    "/{lender_slug}/applications/{application_id}/documents/{document_id}",
)
def delete_public_application_document(
    lender_slug: str,
    application_id: int,
    document_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete an application document from S3 (when applicable) and the database."""
    lender_id = _lender_id_for_slug(db, lender_slug)
    document = get_application_document(
        db,
        document_id,
        lender_id=lender_id,
        application_id=application_id,
    )
    if document.storage_type == "s3" and document.storage_key:
        delete_object(document.storage_key)
    delete_application_document(
        db,
        document_id,
        lender_id=lender_id,
        application_id=application_id,
    )
    return {"message": "Document deleted successfully"}


router.include_router(clients_documents_router)
router.include_router(client_me_router)
router.include_router(apply_documents_router)
