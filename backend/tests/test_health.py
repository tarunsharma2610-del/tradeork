HEALTH_URL = "/api/v1/health"


def test_health_endpoint(client):
    res = client.get(HEALTH_URL)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in ("ok", "degraded")
    assert "database" in body
    assert "redis" in body


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
