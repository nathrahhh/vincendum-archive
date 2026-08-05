from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.schemas import CurrentUserResponse
from app.models.user import UserORM

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=CurrentUserResponse)
def get_me(
    current_user: UserORM = Depends(get_current_user),
) -> CurrentUserResponse:
    """Return the authenticated local user for onboarding and UI gates."""
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        lender_id=current_user.lender_id,
    )
