"""FastAPI dependencies for resolving the authenticated user."""

from fastapi import HTTPException, Request, status

from gerec_api.auth.sessions import AuthService, CurrentUser, InvalidSessionError


SESSION_COOKIE_NAME = "gerec_session"


def get_auth_service(request: Request) -> AuthService:
    """Return the request application's configured authentication service."""
    service = getattr(request.app.state, "auth_service", None)
    if not isinstance(service, AuthService):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    return service


def get_current_user(request: Request) -> CurrentUser:
    """Resolve the current active user from the HTTP-only opaque-session cookie."""
    raw_token = request.cookies.get(SESSION_COOKIE_NAME)
    try:
        return get_auth_service(request).current_user(raw_token or "")
    except InvalidSessionError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        ) from error
