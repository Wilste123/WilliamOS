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


def test_home_requires_auth(client):
    response = client.get("/home")
    assert response.status_code == 401


def test_home_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.overview.build_home_summary",
        lambda display_name=None: {
            "greeting_name": "William",
            "net_worth_nok": 6200000,
            "net_worth_formatted": "6,2 MNOK",
            "active_goals": 3,
            "open_tasks": 17,
            "priorities": ["Mazda etterkontroll", "Tun32", "HouseOS"],
            "metrics": {"projects": 2},
        },
    )
    response = authed_client.get("/home")
    assert response.status_code == 200
    body = response.json()
    assert body["greeting_name"] == "William"
    assert body["net_worth_formatted"] == "6,2 MNOK"
    assert len(body["priorities"]) == 3


def test_dashboard_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.overview.build_dashboard_summary",
        lambda: {"priorities": [], "events": []},
    )
    response = authed_client.get("/dashboard")
    assert response.status_code == 200
    assert "priorities" in response.json()
