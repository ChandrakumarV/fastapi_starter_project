from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi_starter_project.core.dependencies import get_current_user
from fastapi_starter_project.schemas.user import UserInDB, UserResponse

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the currently authenticated user extracted from the HTTP-only cookie.",
)
def get_current_user_profile(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)
