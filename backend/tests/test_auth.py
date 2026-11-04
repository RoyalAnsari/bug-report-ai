import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import create_app
from app.repositories import users as users_repo

SECRET = "t" * 40
ADMIN_PASSWORD = "correct horse battery"
REVIEWER_PASSWORD = "another long password"
ADMIN_HASH = hash_password(ADMIN_PASSWORD)
REVIEWER_HASH = hash_password(REVIEWER_PASSWORD)


def make_user(user_id, email, role, password_hash, is_active=True):
    return {
        "_id": user_id,
        "email": email,
        "name": user_id.title(),
        "role": role,
        "password_hash": password_hash,
        "is_active": is_active,
        "created_at": None,
        "updated_at": None,
        "last_login_at": None,
    }


@pytest.fixture
def users(monkeypatch):
    """Nakli in-memory users, asli MongoDB ke baghair."""
    store = {
        "usr_admin": make_user("usr_admin", "admin@example.com", "admin", ADMIN_HASH),
        "usr_rev": make_user("usr_rev", "reviewer@example.com", "reviewer", REVIEWER_HASH),
    }

    async def get_by_id(db, user_id):
        return store.get(user_id)

    async def get_by_email(db, email):
        wanted = users_repo.normalize_email(email)
        return next((doc for doc in store.values() if doc["email"] == wanted), None)

    async def touch_login(db, user_id):
        return None

    async def create_user(db, email, name, role, password_hash):
        if await get_by_email(db, email):
            return None
        doc = make_user("usr_new" + str(len(store)), users_repo.normalize_email(email), role, password_hash)
        doc["name"] = name
        store[doc["_id"]] = doc
        return doc

    async def list_users(db):
        return list(store.values())

    async def update_user(db, user_id, fields):
        if user_id not in store:
            return None
        store[user_id].update(fields)
        return store[user_id]

    async def set_password(db, user_id, password_hash):
        if user_id not in store:
            return False
        store[user_id]["password_hash"] = password_hash
        return True

    for name, fake in {
        "get_by_id": get_by_id,
        "get_by_email": get_by_email,
        "touch_login": touch_login,
        "create_user": create_user,
        "list_users": list_users,
        "update_user": update_user,
        "set_password": set_password,
    }.items():
        monkeypatch.setattr(users_repo, name, fake)
    return store


@pytest.fixture
def client(users):
    app = create_app(Settings(load_models=False, auth_enabled=True, jwt_secret=SECRET))
    with TestClient(app) as test_client:
        test_client.app.state.db = object()  # asli database nahi, repository functions fake hain
        yield test_client


def login(client, email, password):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client, email="admin@example.com", password=ADMIN_PASSWORD):
    response = login(client, email, password)
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


# ---- password aur token ----


def test_password_hash_roundtrip():
    assert ADMIN_HASH != ADMIN_PASSWORD
    assert verify_password(ADMIN_PASSWORD, ADMIN_HASH) is True
    assert verify_password("wrong password!!", ADMIN_HASH) is False
    assert verify_password(ADMIN_PASSWORD, "not-a-valid-hash") is False


def test_token_roundtrip_and_tampering():
    token = create_access_token("usr_1", "admin", SECRET, 5)
    assert decode_access_token(token, SECRET)["sub"] == "usr_1"
    assert decode_access_token(token, "z" * 40) is None
    assert decode_access_token(token + "x", SECRET) is None
    assert decode_access_token("garbage", SECRET) is None


def test_expired_token_is_rejected():
    from datetime import datetime, timedelta, timezone

    old = datetime.now(timezone.utc) - timedelta(hours=2)
    token = create_access_token("usr_1", "admin", SECRET, 5, now=old)
    assert decode_access_token(token, SECRET) is None


# ---- startup ki jaanch ----


def test_startup_requires_a_strong_secret_when_auth_is_on():
    with pytest.raises(ValueError):
        create_app(Settings(load_models=False, auth_enabled=True, jwt_secret="short"))
    with pytest.raises(ValueError):
        create_app(Settings(load_models=False, auth_enabled=True, jwt_secret=""))


def test_auth_off_needs_no_secret_and_config_says_so():
    app = create_app(Settings(load_models=False, auth_enabled=False))
    with TestClient(app) as test_client:
        assert test_client.get("/api/v1/auth/config").json() == {"auth_enabled": False}


# ---- login ----


def test_login_success_returns_token_and_no_password_hash(client):
    response = login(client, "admin@example.com", ADMIN_PASSWORD)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "admin"
    assert "password_hash" not in response.text
    assert body["expires_in"] == 3600


def test_login_email_is_case_insensitive(client):
    assert login(client, "  ADMIN@Example.com ", ADMIN_PASSWORD).status_code == 200


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    wrong_password = login(client, "admin@example.com", "not the password")
    unknown_email = login(client, "nobody@example.com", "not the password")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_inactive_user_cannot_log_in(client, users):
    users["usr_rev"]["is_active"] = False
    assert login(client, "reviewer@example.com", REVIEWER_PASSWORD).status_code == 401


# ---- routes ki hifazat ----


def test_health_is_public(client):
    assert client.get("/api/v1/health").status_code != 401


def test_protected_route_needs_a_token(client):
    response = client.get("/api/v1/reports")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == 401


def test_bad_token_is_rejected(client):
    response = client.get("/api/v1/reports", headers={"Authorization": "Bearer not-a-token"})
    assert response.status_code == 401


def test_me_returns_current_user(client):
    response = client.get("/api/v1/auth/me", headers=auth_headers(client))
    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_deactivated_user_token_stops_working(client, users):
    headers = auth_headers(client, "reviewer@example.com", REVIEWER_PASSWORD)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    users["usr_rev"]["is_active"] = False
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_role_comes_from_database_not_from_token(client, users):
    headers = auth_headers(client, "reviewer@example.com", REVIEWER_PASSWORD)
    users["usr_rev"]["role"] = "admin"
    assert client.get("/api/v1/users", headers=headers).status_code == 200


def test_reviewer_cannot_use_admin_routes(client):
    headers = auth_headers(client, "reviewer@example.com", REVIEWER_PASSWORD)
    assert client.get("/api/v1/users", headers=headers).status_code == 403
    assert client.delete("/api/v1/reports/br_x", headers=headers).status_code == 403
    assert client.post(
        "/api/v1/reports", headers=headers, json={"text": "Crash on save", "project": "Core", "severity": "major"}
    ).status_code == 403


# ---- users (admin) ----


def test_admin_creates_user_and_duplicate_email_is_rejected(client):
    headers = auth_headers(client)
    payload = {"email": "New@Example.com", "name": "New User", "role": "reviewer", "password": "a very long password"}
    created = client.post("/api/v1/users", headers=headers, json=payload)
    assert created.status_code == 201
    assert created.json()["email"] == "new@example.com"
    assert "password" not in created.text
    assert client.post("/api/v1/users", headers=headers, json=payload).status_code == 409


def test_short_password_is_rejected(client):
    headers = auth_headers(client)
    payload = {"email": "x@example.com", "name": "X", "role": "reviewer", "password": "short"}
    assert client.post("/api/v1/users", headers=headers, json=payload).status_code == 422


def test_admin_cannot_demote_or_deactivate_self(client):
    headers = auth_headers(client)
    assert client.patch("/api/v1/users/usr_admin", headers=headers, json={"role": "reviewer"}).status_code == 400
    assert client.patch("/api/v1/users/usr_admin", headers=headers, json={"is_active": False}).status_code == 400


def test_admin_can_change_another_users_role(client):
    headers = auth_headers(client)
    response = client.patch("/api/v1/users/usr_rev", headers=headers, json={"role": "admin"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


# ---- password badalna ----


def test_change_password_flow(client):
    headers = auth_headers(client, "reviewer@example.com", REVIEWER_PASSWORD)
    wrong = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "wrong password", "new_password": "a brand new password"},
    )
    assert wrong.status_code == 400
    ok = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": REVIEWER_PASSWORD, "new_password": "a brand new password"},
    )
    assert ok.status_code == 204
    assert login(client, "reviewer@example.com", REVIEWER_PASSWORD).status_code == 401
    assert login(client, "reviewer@example.com", "a brand new password").status_code == 200
