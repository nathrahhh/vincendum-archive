from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    AuthenticatedAuth0Identity,
    get_authenticated_auth0_identity,
)
from app.db import get_db
from app.models.schemas import (
    ClientInvitationAcceptRequest,
    ClientInvitationAcceptResponse,
)
from app.services.client_invitation_service import accept_client_invitation

router = APIRouter(prefix="/client-invitations", tags=["client-invitations"])


@router.post("/accept", response_model=ClientInvitationAcceptResponse)
def accept_invitation(
    payload: ClientInvitationAcceptRequest,
    db: Session = Depends(get_db),
    identity: AuthenticatedAuth0Identity = Depends(get_authenticated_auth0_identity),
) -> ClientInvitationAcceptResponse:
    """
    Accept a client invitation for the authenticated Auth0 user.

    Creates/updates the local user as a client. ``client_id`` and ``lender_id``
    come only from the invitation matched by token hash.
    """
    invitation, client, user = accept_client_invitation(
        db,
        auth0_user_id=identity.auth0_user_id,
        email=identity.email,
        raw_token=payload.token,
    )
    return ClientInvitationAcceptResponse(
        invitation_id=invitation.id,
        client_id=client.id,
        client_name=client.name,
        status=invitation.status,
        role=user.role,
    )
