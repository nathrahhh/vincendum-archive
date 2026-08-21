"""Document metadata and ownership service.

Persists ``DocumentORM`` rows and enforces lender/client/application
ownership. File bytes live in S3 under ``storage_key``; this module does
not generate presigned URLs or talk to AWS directly.

Lifecycle
---------
Before application approval:

    lender_id = application.lender_id
    application_id = application.id
    client_id = NULL

After application approval:

    lender_id = application.lender_id
    application_id = application.id
    client_id = newly_created_client.id

The S3 object key is unchanged; the file is never moved in storage.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import ClientORM
from app.models.client_application import ClientApplicationORM
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


def _application_for_lender_or_404(
    db: Session,
    application_id: int,
    lender_id: int,
) -> ClientApplicationORM:
    application = db.execute(
        select(ClientApplicationORM).where(
            ClientApplicationORM.id == application_id,
            ClientApplicationORM.lender_id == lender_id,
        )
    ).scalar_one_or_none()
    if application is None:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found",
        )
    return application


def _get_client_document_or_404(
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


def _get_application_document_or_404(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    application_id: int,
) -> DocumentORM:
    row = db.execute(
        select(DocumentORM).where(
            DocumentORM.id == document_id,
            DocumentORM.lender_id == lender_id,
            DocumentORM.application_id == application_id,
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
    row = _get_client_document_or_404(
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
    """Delete one client document when lender and client ownership both match."""
    row = _get_client_document_or_404(
        db,
        document_id,
        lender_id=lender_id,
        client_id=client_id,
    )
    db.delete(row)
    db.commit()


def get_application_documents(
    db: Session,
    *,
    lender_id: int,
    application_id: int,
) -> list[DocumentRecord]:
    """Return documents attached to an application owned by ``lender_id``."""
    _application_for_lender_or_404(db, application_id, lender_id)
    rows = db.execute(
        select(DocumentORM)
        .where(
            DocumentORM.lender_id == lender_id,
            DocumentORM.application_id == application_id,
        )
        .order_by(DocumentORM.id.desc())
    ).scalars().all()
    return [_to_record(row) for row in rows]


def create_application_document(
    db: Session,
    *,
    lender_id: int,
    application_id: int,
    name: str,
    storage_key: str,
    storage_type: str = "s3",
) -> DocumentRecord:
    """
    Create a document attached to a pending application.

    ``client_id`` remains ``NULL`` until the application is approved.
    ``lender_id`` must come from the authenticated/public lender context,
    not from a user-supplied payload.
    """
    application = _application_for_lender_or_404(db, application_id, lender_id)
    trimmed_name = name.strip()
    trimmed_key = storage_key.strip()
    if not trimmed_name:
        raise HTTPException(status_code=422, detail="Document name is required")
    if not trimmed_key:
        raise HTTPException(status_code=422, detail="storage_key is required")

    document = DocumentORM(
        lender_id=application.lender_id,
        application_id=application.id,
        client_id=None,
        name=trimmed_name,
        storage_type=storage_type,
        storage_key=trimmed_key,
        external_url=None,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _to_record(document)


def get_application_document(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    application_id: int,
) -> DocumentRecord:
    """Return one application document when lender and application ownership match."""
    _application_for_lender_or_404(db, application_id, lender_id)
    row = _get_application_document_or_404(
        db,
        document_id,
        lender_id=lender_id,
        application_id=application_id,
    )
    return _to_record(row)


def delete_application_document(
    db: Session,
    document_id: int,
    *,
    lender_id: int,
    application_id: int,
) -> None:
    """Delete one application document when lender and application ownership match."""
    _application_for_lender_or_404(db, application_id, lender_id)
    row = _get_application_document_or_404(
        db,
        document_id,
        lender_id=lender_id,
        application_id=application_id,
    )
    db.delete(row)
    db.commit()


def assign_application_documents_to_client(
    db: Session,
    *,
    lender_id: int,
    application_id: int,
    client_id: int,
) -> int:
    """
    Attach application documents to a newly created client after approval.

    Sets ``client_id`` while keeping ``application_id`` and ``storage_key``
    unchanged. Does not move or copy objects in S3.

    Returns:
        The number of documents updated.
    """
    documents = db.execute(
        select(DocumentORM).where(
            DocumentORM.application_id == application_id,
            DocumentORM.lender_id == lender_id,
        )
    ).scalars().all()
    for document in documents:
        document.application_id = None
        document.client_id = client_id
    return len(documents)
