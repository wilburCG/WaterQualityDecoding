"""安全模块单测：密码哈希与 JWT。"""
import jwt
import pytest

from app.core import security


def test_password_hash_roundtrip():
    h = security.hash_password("my-secret")
    assert h != "my-secret"
    assert security.verify_password("my-secret", h)
    assert not security.verify_password("wrong", h)


def test_password_hash_unique_salt():
    assert security.hash_password("same") != security.hash_password("same")


def test_verify_bad_format():
    assert not security.verify_password("x", "garbage")
    assert not security.verify_password("x", "algo$x$y$z")


def test_jwt_roundtrip():
    token = security.create_access_token(42, "user")
    payload = security.decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "user"


def test_jwt_tampered():
    token = security.create_access_token(1, "user")
    with pytest.raises(jwt.PyJWTError):
        security.decode_token(token + "x")
