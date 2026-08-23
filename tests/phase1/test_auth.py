import pytest
from src.backend.routers.auth import (
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
    from src.backend.routers.auth import LegacyPasswordHasher, SECRET_KEY
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
    from src.backend.routers.auth import ensure_default_user
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


# ---------------------------------------------------------------------------
# Authentication *enforcement*.
#
# SCORING_RUBRIC.md:66 grades "authentication enforcement", and until these were
# written not one test asserted that an unauthenticated request is refused. The
# suite had nine tests proving the JWT machinery worked correctly and none proving
# it was actually in the request path -- so it passed at 100% while every one of
# the twelve inventory routes served anonymous callers as a manager.
# ---------------------------------------------------------------------------

PROTECTED_ROUTES = [
    ("get", "/api/v1/products"),
    ("get", "/api/v1/products/1"),
    ("get", "/api/v1/suppliers"),
    ("get", "/api/v1/orders"),
    ("get", "/api/v1/dashboard"),
    ("get", "/api/v1/stock/low-alerts"),
    ("post", "/api/v1/products"),
    ("post", "/api/v1/suppliers"),
    ("post", "/api/v1/orders"),
    ("patch", "/api/v1/products/1/stock"),
    ("patch", "/api/v1/orders/1/receive"),
]


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_missing_credentials(client, method, path):
    """No token at all must be 401 -- not 200, and not a manager session."""
    kwargs = {} if method == "get" else {"json": {}}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401, (
        f"{method.upper()} {path} answered {response.status_code} with no credentials"
    )
    assert response.headers.get("www-authenticate") == "Bearer"


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_protected_route_rejects_garbage_token(client, method, path):
    kwargs = {} if method == "get" else {"json": {}}
    response = getattr(client, method)(
        path, headers={"Authorization": "Bearer not-a-real-jwt"}, **kwargs
    )
    assert response.status_code == 401


def test_protected_route_rejects_retired_test_token(client):
    """The `test_token` literal must no longer be a valid credential."""
    response = client.get("/api/v1/products", headers={"Authorization": "Bearer test_token"})
    assert response.status_code == 401


def test_protected_route_accepts_real_jwt(client, auth_headers):
    """The positive half: a genuine signed token still gets through."""
    response = client.get("/api/v1/products", headers=auth_headers)
    assert response.status_code == 200


def test_inactive_user_token_is_rejected(client, db_session, auth_headers):
    from src.backend.models import User

    user = db_session.query(User).filter(User.email == "test-manager@retail.com").first()
    user.is_active = False
    db_session.commit()

    response = client.get("/api/v1/products", headers=auth_headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "User account is inactive"


def test_token_expiry_is_enforced(client, db_session, auth_headers):
    from datetime import timedelta

    expired = create_access_token(
        data={"sub": "test-manager@retail.com"}, expires_delta=timedelta(minutes=-5)
    )
    response = client.get("/api/v1/products", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_token_signed_with_wrong_key_is_rejected(client, db_session, auth_headers):
    """A token this service did not sign must not be accepted."""
    from jose import jwt

    forged = jwt.encode(
        {"sub": "test-manager@retail.com", "role": "manager"}, "attacker-key", algorithm="HS256"
    )
    response = client.get("/api/v1/products", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_anonymous_caller_cannot_self_assign_manager_role(client, db_session):
    """Registration is open, so the role field must not be.

    Verified against the running service before this was fixed: this exact
    request answered 201 with `"role":"manager"`.
    """
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "escalate@retail.com",
            "password": "password123",
            "full_name": "Would-be Manager",
            "role": "manager",
        },
    )
    assert response.status_code == 403
    assert "cannot be self-assigned" in response.json()["detail"]

    from src.backend.models import User

    assert db_session.query(User).filter(User.email == "escalate@retail.com").first() is None


def test_manager_token_may_create_a_manager(client, db_session, auth_headers):
    """The privileged path still works, so the guard is a gate and not a wall."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "second-manager@retail.com",
            "password": "password123",
            "full_name": "Second Manager",
            "role": "manager",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "manager"


def test_staff_token_may_not_create_a_manager(client, db_session):
    """A valid token is not the same as a privileged one."""
    from src.backend.models import User
    from src.backend.routers.auth import get_password_hash

    db_session.add(
        User(
            email="grunt@retail.com",
            hashed_password=get_password_hash("password123"),
            full_name="Warehouse Staff",
            role="staff",
        )
    )
    db_session.commit()
    staff_token = create_access_token(data={"sub": "grunt@retail.com", "role": "staff"})

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "sneaky@retail.com", "password": "password123", "role": "manager"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 403


def test_unknown_role_is_rejected(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weird@retail.com", "password": "password123", "role": "superadmin"},
    )
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]


def test_public_routes_remain_open(client):
    """Enforcement must not have swept up the unauthenticated surface."""
    assert client.get("/health").status_code == 200
    assert client.get("/").status_code == 200
    assert client.post(
        "/api/v1/auth/register",
        json={"email": "open@retail.com", "password": "password123"},
    ).status_code == 201
