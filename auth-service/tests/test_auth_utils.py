from datetime import datetime, timezone

import pytest
from jose import JWTError, jwt

from app.auth_utils import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_HOURS,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_bcrypt_hash():
    hashed = hash_password("mysecret")
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    hashed = hash_password("correcthorsebatterystaple")
    assert verify_password("correcthorsebatterystaple", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correctpassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token_contains_all_claims():
    token = create_access_token("user123", "test@example.com", "sender")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "sender"
    assert "iat" in payload
    assert "exp" in payload


def test_create_access_token_expires_in_24h():
    token = create_access_token("user123", "test@example.com", "courier")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["exp"] - payload["iat"] == ACCESS_TOKEN_EXPIRE_HOURS * 3600


def test_decode_token_valid_roundtrip():
    token = create_access_token("abc", "a@b.com", "sender")
    payload = decode_token(token)
    assert payload["sub"] == "abc"
    assert payload["email"] == "a@b.com"
    assert payload["role"] == "sender"


def test_decode_token_wrong_secret_raises():
    token = jwt.encode({"sub": "x"}, "wrong-secret", algorithm=ALGORITHM)
    with pytest.raises(JWTError):
        decode_token(token)


def test_decode_token_expired_raises():
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "x",
        "iat": now - timedelta(hours=48),
        "exp": now - timedelta(hours=24),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(JWTError):
        decode_token(token)
