def test_create_asset_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.assets.create_asset_record",
        lambda payload: {"id": "asset-1", "name": payload.get("name"), "status": payload.get("status")},
    )
    response = authed_client.post("/assets", json={"name": "Mazda", "status": "active"})
    assert response.status_code == 200
    assert response.json()["name"] == "Mazda"


def test_asset_detail_requires_auth(client):
    response = client.get("/assets/test-id")
    assert response.status_code == 401


def test_asset_detail_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.assets.get_asset_detail",
        lambda asset_id: {
            "asset": {"id": asset_id, "name": "Tun32"},
            "tasks": [],
            "open_tasks": [],
            "projects": [],
            "documents": [],
            "decisions": [],
            "events": [],
        },
    )
    response = authed_client.get("/assets/asset-1")
    assert response.status_code == 200
    assert response.json()["asset"]["name"] == "Tun32"


def test_asset_detail_not_found(authed_client, monkeypatch):
    monkeypatch.setattr("app.api.routes.assets.get_asset_detail", lambda asset_id: None)
    response = authed_client.get("/assets/missing")
    assert response.status_code == 404


def test_chat_history_requires_auth(client):
    response = client.get("/chat/history")
    assert response.status_code == 401


def test_chat_history_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.chat.list_chat_messages",
        lambda limit=40: [{"role": "user", "content": "Hei"}],
    )
    response = authed_client.get("/chat/history")
    assert response.status_code == 200
    assert response.json()["messages"][0]["content"] == "Hei"


def test_usage_requires_auth(client):
    response = client.get("/usage")
    assert response.status_code == 401


def test_usage_open_with_auth(authed_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.usage.record_app_open",
        lambda: {
            "days_opened_this_week": 1,
            "total_opens": 1,
            "streak_days": 1,
            "last_opened_at": "2026-08-17",
            "seven_day_goal_met": False,
        },
    )
    response = authed_client.post("/usage/open")
    assert response.status_code == 200
    assert response.json()["days_opened_this_week"] == 1
