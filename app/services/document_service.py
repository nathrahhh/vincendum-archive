"""Client document metadata service.

Persists DocumentORM rows for existing clients and enforces lender/client
ownership. Does not upload files, generate signed URLs, or handle
application-scoped documents.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.document import DocumentORM
from app.models.schemas import DocumentCreate, DocumentRecord


def _to_record(row: DocumentORM) -> DocumentRecord:
    return DocumentRecord(
        id=row.id,
        lender_id=row.lender_id,
        client_id=row.client_id,
        application_id=row.application_id,
        name=row.name,
        storage_type=row.storage_type,
        storage_key=row.storage_key,
        external_url=row.external_url,
        created_at=row.created_at,
    )


def _client_for_lender_or_404(
    db: Session,
    client_id: int,
    lender_id: int,
) -> ClientORM:
    client = db.execute(
        select(ClientORM).where(
            ClientORM.id == client_id,
            ClientORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if client is None:
        raise HTTPException(
            status_code=404,
            detail=f"Client {client_id} not found",
        )
    return client


def _get_document_or_404(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    client_id: int,
) -> DocumentORM:
    row = db.execute(
        select(DocumentORM).where(
            DocumentORM.id == document_id,
            DocumentORM.lender_id == lender_id,
            DocumentORM.client_id == client_id,
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found",
        )
    return row


def get_client_documents(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
) -> list[DocumentRecord]:
    """Return documents owned by the authenticated client."""
    rows = db.execute(
        select(DocumentORM)
        .where(
            DocumentORM.lender_id == lender_id,
            DocumentORM.client_id == client_id,
        )
        .order_by(DocumentORM.id.desc())
    ).scalars().all()
    return [_to_record(row) for row in rows]


def get_lender_client_documents(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
) -> list[DocumentRecord]:
    """Return documents for a client owned by the authenticated lender."""
    _client_for_lender_or_404(db, client_id, lender_id)
    return get_client_documents(
        db,
        lender_id=lender_id,
        client_id=client_id,
    )


def create_client_document(
    db: Session,
    *,
    current_client: ClientORM,
    payload: DocumentCreate,
) -> DocumentRecord:
    """
    Create a document owned by ``current_client``.

    Ownership comes only from the authenticated client profile.
    """
    if current_client.lender_id is None:
        raise HTTPException(
            status_code=403,
            detail="Client is not assigned to a lender",
        )

    document = DocumentORM(
        lender_id=current_client.lender_id,
        client_id=current_client.id,
        application_id=None,
        name=payload.name.strip(),
        storage_type=payload.storage_type,
        storage_key=payload.storage_key,
        external_url=payload.external_url,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _to_record(document)


def create_lender_client_document(
    db: Session,
    *,
    lender_id: int,
    client_id: int,
    payload: DocumentCreate,
) -> DocumentRecord:
    """Create a document for a client belonging to the authenticated lender."""
    _client_for_lender_or_404(db, client_id, lender_id)

    document = DocumentORM(
        lender_id=lender_id,
        client_id=client_id,
        application_id=None,
        name=payload.name.strip(),
        storage_type=payload.storage_type,
        storage_key=payload.storage_key,
        external_url=payload.external_url,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _to_record(document)


def get_document(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    client_id: int,
) -> DocumentRecord:
    """Return one document when lender and client ownership both match."""
    row = _get_document_or_404(
        db,
        document_id,
        lender_id=lender_id,
        client_id=client_id,
    )
    return _to_record(row)


def delete_document(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    client_id: int,
) -> None:
    """Delete one document when lender and client ownership both match."""
    row = _get_document_or_404(
        db,
        document_id,
        lender_id=lender_id,
        client_id=client_id,
    )
    db.delete(row)
    db.commit()
