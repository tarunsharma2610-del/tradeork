VALID_PASSWORD = "Str0ng!Passw0rd"
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"


def register_user(client, email: str, full_name: str = "Test User"):
    res = client.post(
        REGISTER_URL,
        json={
            "email": email,
            "password": VALID_PASSWORD,
            "full_name": full_name,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def login_user(client, email: str):
    res = client.post(
        LOGIN_URL,
        json={"email": email, "password": VALID_PASSWORD},
    )
    assert res.status_code == 200, res.text
    return res.json()


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
