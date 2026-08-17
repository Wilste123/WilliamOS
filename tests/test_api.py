def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_requires_auth(client):
    response = client.get("/dashboard")
    assert response.status_code == 401


def test_chat_requires_auth(client):
    response = client.post("/chat/", json={"message": "Hei"})
    assert response.status_code == 401


def test_dashboard_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.overview.build_dashboard_summary",
        lambda: {"priorities": [], "events": []},
    )
    response = authed_client.get("/dashboard")
    assert response.status_code == 200
    assert "priorities" in response.json()
