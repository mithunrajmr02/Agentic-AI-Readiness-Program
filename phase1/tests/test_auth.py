import pytest
from app.routers.auth import (
    get_password_hash, verify_password, create_access_token, get_current_user
)
from fastapi import HTTPException


def test_password_hashing():
    password = "secretpassword123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_legacy_password_verification():
    import os
    import hashlib
    from app.routers.auth import LegacyPasswordHasher, SECRET_KEY
    hasher = LegacyPasswordHasher()
    salt = os.getenv("PASSWORD_SALT", SECRET_KEY).encode("utf-8")
    legacy_hash = hashlib.pbkdf2_hmac("sha256", b"admin", salt, 100_000).hex()
    assert hasher.verify("admin", legacy_hash) is True
    assert verify_password("admin", legacy_hash) is True



def test_register_user_success(client, db_session):
    payload = {
        "email": "newuser@retail.com",
        "password": "password123",
        "full_name": "New User",
        "role": "staff"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@retail.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "staff"


def test_register_user_duplicate_email(client, db_session):
    payload = {
        "email": "duplicate@retail.com",
        "password": "password123",
        "full_name": "User One"
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    assert res2.json()["detail"] == "Email already registered"


def test_login_success(client, db_session):
    client.post("/api/v1/auth/register", json={
        "email": "loginuser@retail.com",
        "password": "securepassword",
        "full_name": "Login User"
    })

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser@retail.com", "password": "securepassword"}
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, db_session):
    client.post("/api/v1/auth/register", json={
        "email": "valid@retail.com",
        "password": "correctpassword"
    })

    # Wrong password
    res1 = client.post(
        "/api/v1/auth/login",
        data={"username": "valid@retail.com", "password": "wrongpassword"}
    )
    assert res1.status_code == 401

    # Non-existent email
    res2 = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@retail.com", "password": "correctpassword"}
    )
    assert res2.status_code == 401


def test_get_current_user_with_valid_jwt(db_session):
    from app.routers.auth import ensure_default_user
    ensure_default_user(db_session)
    token = create_access_token(data={"sub": "admin@retail.com"})
    user = get_current_user(token=f"Bearer {token}", db=db_session)
    assert user.email == "admin@retail.com"



def test_get_current_user_invalid_token(db_session):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid_jwt_token", db=db_session)
    assert exc_info.value.status_code == 401


def test_get_current_user_user_not_found(db_session):
    token = create_access_token(data={"sub": "ghost@retail.com"})
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token=f"Bearer {token}", db=db_session)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User not found"
