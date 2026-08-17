

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
LOGOUT_URL = "/api/v1/auth/logout"
ME_URL = "/api/v1/users/me"

VALID_PASSWORD = "Str0ng!Passw0rd"


def _register(client, email: str = "alice@example.com", password: str = VALID_PASSWORD):
    return client.post(
        REGISTER_URL,
        json={"email": email, "password": password, "full_name": "Alice"},
    )


def test_register_success(client):
    res = _register(client)
    assert res.status_code == 201
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_in"] > 0


def test_register_duplicate_email(client):
    assert _register(client).status_code == 201
    res = _register(client)
    assert res.status_code == 409
    assert "already exists" in res.json()["detail"]


def test_register_rejects_weak_password(client):
    res = client.post(
        REGISTER_URL,
        json={"email": "bob@example.com", "password": "short", "full_name": "Bob"},
    )
    assert res.status_code == 422


def test_register_rejects_invalid_email(client):
    res = client.post(
        REGISTER_URL,
        json={"email": "not-an-email", "password": VALID_PASSWORD},
    )
    assert res.status_code == 422


def test_login_success(client):
    _register(client)
    res = client.post(
        LOGIN_URL,
        json={"email": "alice@example.com", "password": VALID_PASSWORD},
    )
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_login_wrong_password(client):
    _register(client)
    res = client.post(
        LOGIN_URL,
        json={"email": "alice@example.com", "password": "WrongPass123"},
    )
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post(
        LOGIN_URL,
        json={"email": "ghost@example.com", "password": VALID_PASSWORD},
    )
    assert res.status_code == 401


def test_email_is_normalised(client):
    _register(client, email="CaseUser@Example.com")
    res = client.post(
        LOGIN_URL,
        json={"email": "caseuser@example.com", "password": VALID_PASSWORD},
    )
    assert res.status_code == 200


def test_me_requires_auth(client):
    res = client.get(ME_URL)
    assert res.status_code == 401


def test_me_rejects_refresh_token_as_access(client):
    reg = _register(client).json()
    res = client.get(ME_URL, headers={"Authorization": f"Bearer {reg['refresh_token']}"})
    assert res.status_code == 401


def test_me_with_valid_token(client):
    reg = _register(client).json()
    res = client.get(ME_URL, headers={"Authorization": f"Bearer {reg['access_token']}"})
    assert res.status_code == 200
    body = res.json()
    assert body["email"] == "alice@example.com"
    assert body["full_name"] == "Alice"
    assert body["is_active"] is True


def test_refresh_rotates_token(client):
    reg = _register(client).json()
    res = client.post(REFRESH_URL, json={"refresh_token": reg["refresh_token"]})
    assert res.status_code == 200
    new_tokens = res.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"] != reg["refresh_token"]


def test_refresh_token_reuse_rejected(client):
    reg = _register(client).json()
    old_refresh = reg["refresh_token"]
    assert client.post(REFRESH_URL, json={"refresh_token": old_refresh}).status_code == 200
    res = client.post(REFRESH_URL, json={"refresh_token": old_refresh})
    assert res.status_code == 401


def test_refresh_missing_token(client):
    res = client.post(REFRESH_URL, json={})
    assert res.status_code == 401


def test_logout_revokes_refresh_token(client):
    reg = _register(client).json()
    res = client.post(LOGOUT_URL, json={"refresh_token": reg["refresh_token"]})
    assert res.status_code == 204
    refresh = client.post(REFRESH_URL, json={"refresh_token": reg["refresh_token"]})
    assert refresh.status_code == 401


def test_audit_log_written_on_register(client, db_session):
    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    _register(client)
    logs = list(
        db_session.scalars(select(AuditLog).where(AuditLog.action == "auth.register"))
    )
    assert len(logs) == 1
    assert logs[0].resource_type == "user"
    assert logs[0].resource_id

