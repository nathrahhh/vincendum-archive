from app.models.client_invitation import INVITATION_STATUSES, ClientInvitationORM


def test_client_invitation_tablename():
    assert ClientInvitationORM.__tablename__ == "client_invitations"


def test_client_invitation_required_columns_exist():
    columns = set(ClientInvitationORM.__table__.columns.keys())
    assert columns == {
        "id",
        "lender_id",
        "client_id",
        "email",
        "token_hash",
        "status",
        "created_at",
        "expires_at",
        "accepted_at",
    }


def test_client_invitation_token_hash_is_unique():
    assert ClientInvitationORM.__table__.c.token_hash.unique is True


def test_invitation_statuses():
    assert INVITATION_STATUSES == (
        "pending",
        "accepted",
        "expired",
        "cancelled",
    )
