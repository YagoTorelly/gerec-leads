"""Unit coverage for password hashing boundaries."""

from gerec_api.auth.passwords import hash_password, verify_password


def test_hash_password_uses_argon2id_and_never_returns_the_plaintext() -> None:
    """Breaks if a password can be stored as plaintext or with another Argon2 variant."""
    password = "Senha-inicial-2026!"

    digest = hash_password(password)

    assert digest != password
    assert digest.startswith("$argon2id$")
    assert "m=" in digest
    assert verify_password(password, digest) is True


def test_verify_password_rejects_an_incorrect_or_malformed_digest() -> None:
    """Breaks if invalid credentials can authenticate or a damaged record crashes login."""
    digest = hash_password("Senha-inicial-2026!")

    assert verify_password("senha-errada", digest) is False
    assert verify_password("Senha-inicial-2026!", "not-an-argon2-digest") is False
