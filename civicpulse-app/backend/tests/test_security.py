import jwt
import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify():
    hashed = hash_password("Secret123")
    assert hashed != "Secret123"
    assert verify_password("Secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_token_round_trip():
    token = create_access_token(7, "officer")
    payload = decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "officer"


def test_bad_token_is_rejected():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("not-a-real-token")
