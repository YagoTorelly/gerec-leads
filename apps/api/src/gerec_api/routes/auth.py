"""HTTP endpoints for login, logout, and current-session identity."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from gerec_api.auth.dependencies import SESSION_COOKIE_NAME, get_auth_service, get_current_user
from gerec_api.auth.sessions import AuthService, CurrentUser, InvalidCredentialsError, SESSION_DURATION


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class CurrentUserResponse(BaseModel):
    id: str
    email: str
    role: str


class LoginResponse(BaseModel):
    user: CurrentUserResponse


def _public_user(user: CurrentUser) -> CurrentUserResponse:
    return CurrentUserResponse(id=user.id, email=user.email, role=user.role)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Set a secure HTTP-only cookie after a successful credentials check."""
    try:
        result = service.login(payload.email, payload.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from error

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result.raw_token,
        max_age=int(SESSION_DURATION.total_seconds()),
        expires=result.expires_at,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )
    return LoginResponse(user=_public_user(result.user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, service: AuthService = Depends(get_auth_service)) -> None:
    """Revoke the server session and remove the browser cookie, even if it is already invalid."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    if raw_token:
        service.logout(raw_token)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUserResponse:
    """Return only the public identity associated with the active session."""
    return _public_user(current_user)
