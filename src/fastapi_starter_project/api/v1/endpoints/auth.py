from fastapi import APIRouter, HTTPException, Response, status
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.core.security import create_access_token
from fastapi_starter_project.schemas.auth import LoginRequest
from fastapi_starter_project.schemas.common import MessageResponse
from fastapi_starter_project.services.user_service import user_service

router = APIRouter()


@router.post(
    "/login",
    response_model=MessageResponse,
    summary="User login",
    description="Authenticates credentials and sets an HTTP-only JWT cookie.",
)
def login(credentials: LoginRequest, response: Response) -> MessageResponse:
    user = user_service.authenticate(
        username=credentials.username,
        password=credentials.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        )

    token = create_access_token(subject=user.username)

    max_age_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )

    return MessageResponse(message="Login successful.")


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Clears the HTTP-only JWT authentication cookie.",
)
def logout(response: Response) -> MessageResponse:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path="/",
    )
    return MessageResponse(message="Logged out successfully.")
