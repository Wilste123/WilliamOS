"""Tests for finance, health, and integration services."""

from unittest.mock import patch


def test_compute_net_worth():
    from app.services.finance_service import compute_net_worth

    assets = [{"estimated_value": 5_000_000}]
    accounts = [
        {"account_type": "liquidity", "balance_nok": 200_000},
        {"account_type": "debt", "balance_nok": 300_000},
    ]

    with patch("app.services.finance_service._safe_list") as mock_list:
        mock_list.side_effect = lambda collection: {
            "assets": assets,
            "finance_accounts": accounts,
            "finance_snapshots": [],
        }[collection]

        summary = compute_net_worth()

    assert summary["physical_assets_nok"] == 5_000_000
    assert summary["liquidity_nok"] == 200_000
    assert summary["debt_nok"] == 300_000
    assert summary["net_worth_nok"] == 4_900_000


def test_build_health_summary_empty():
    from app.services.health_service import build_health_summary

    with patch("app.services.health_service._safe_list", return_value=[]):
        with patch("app.services.health_service.list_records", return_value=[]):
            summary = build_health_summary()

    assert summary["latest_weight_kg"] is None
    assert summary["recent_metrics"] == []


def test_list_integration_statuses():
    from app.services.integration_service import list_integration_statuses

    with patch("app.services.integration_service._user_integrations", return_value=[]):
        statuses = list_integration_statuses()

    providers = {row["provider"] for row in statuses}
    assert "outlook" in providers
    assert "apple_health" in providers
    assert "garmin" in providers
    assert "strava" in providers


def test_microsoft_redirect_uri():
    import os

    from app.services.outlook_service import _redirect_uri

    with patch.dict(os.environ, {"FRONTEND_URL": "http://localhost:3000"}, clear=False):
        assert _redirect_uri() == "http://localhost:3000/integrations/callback"
