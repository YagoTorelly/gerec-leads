"""Password hashing backed by Argon2id."""

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError


_PASSWORD_HASHER = PasswordHasher(type=Type.ID)
_DUMMY_PASSWORD_DIGEST = _PASSWORD_HASHER.hash("invalid-password-used-to-equalize-login-work")


def hash_password(password: str) -> str:
    """Return an Argon2id digest; callers must persist only this value."""
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, digest: str) -> bool:
    """Return whether a candidate password matches a valid Argon2 digest."""
    try:
        return _PASSWORD_HASHER.verify(digest, password)
    except (InvalidHashError, VerificationError):
        return False


def verify_unknown_password(password: str) -> None:
    """Consume equivalent Argon2 work when an account cannot authenticate."""
    verify_password(password, _DUMMY_PASSWORD_DIGEST)
