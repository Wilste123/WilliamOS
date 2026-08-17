"""Finance summary, accounts, and net worth tracking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.action_engine import append_event, format_net_worth_nok
from app.services.storage_service import create_record, list_records, update_record


def _safe_list(collection: str) -> list[dict]:
    try:
        return list_records(collection)
    except Exception:
        return []


def _sum_accounts(accounts: list[dict], account_type: str) -> float:
    return sum(float(item.get("balance_nok") or 0) for item in accounts if item.get("account_type") == account_type)


def compute_net_worth() -> dict:
    """Net worth = physical assets + finance assets + liquidity − debt."""
    assets = _safe_list("assets")
    accounts = _safe_list("finance_accounts")

    physical_assets = sum(float(asset.get("estimated_value") or 0) for asset in assets)
    finance_assets = _sum_accounts(accounts, "asset")
    liquidity = _sum_accounts(accounts, "liquidity")
    debt = _sum_accounts(accounts, "debt")

    net_worth = physical_assets + finance_assets + liquidity - debt

    snapshots = sorted(
        _safe_list("finance_snapshots"),
        key=lambda row: row.get("recorded_at") or row.get("created_at") or "",
    )
    change_12m: float | None = None
    if snapshots:
        cutoff = datetime.now(timezone.utc) - timedelta(days=365)
        old = next(
            (
                float(row.get("net_worth_nok") or 0)
                for row in snapshots
                if (row.get("recorded_at") or row.get("created_at") or "")[:10]
                and datetime.fromisoformat(
                    str(row.get("recorded_at") or row.get("created_at")).replace("Z", "+00:00")
                )
                <= cutoff
            ),
            None,
        )
        if old is not None:
            change_12m = net_worth - old
        elif len(snapshots) >= 2:
            change_12m = net_worth - float(snapshots[0].get("net_worth_nok") or 0)

    return {
        "net_worth_nok": net_worth,
        "net_worth_formatted": format_net_worth_nok(net_worth) if net_worth else "—",
        "physical_assets_nok": physical_assets,
        "finance_assets_nok": finance_assets,
        "liquidity_nok": liquidity,
        "debt_nok": debt,
        "change_12m_nok": change_12m,
        "change_12m_formatted": format_net_worth_nok(change_12m) if change_12m is not None else None,
        "accounts": accounts,
    }


def create_finance_account(payload: dict) -> dict:
    account = create_record("finance_accounts", payload)
    append_event(
        title=f"Finanskonto opprettet: {account['name']}",
        event_type="finance_account_created",
        notes=f"{account.get('account_type')} · {account.get('balance_nok')} NOK",
    )
    _maybe_snapshot()
    return account


def update_finance_account(account_id: str, updates: dict) -> dict | None:
    account = update_record("finance_accounts", account_id, updates)
    if account:
        append_event(
            title=f"Finanskonto oppdatert: {account['name']}",
            event_type="finance_account_updated",
        )
        _maybe_snapshot()
    return account


def create_finance_snapshot(net_worth_nok: float, recorded_at: datetime | None = None) -> dict:
    payload: dict = {"net_worth_nok": net_worth_nok}
    if recorded_at:
        payload["recorded_at"] = recorded_at.isoformat()
    return create_record("finance_snapshots", payload)


def _maybe_snapshot() -> None:
    """Keep a lightweight history — at most one auto-snapshot per day."""
    summary = compute_net_worth()
    today = datetime.now(timezone.utc).date().isoformat()
    snapshots = _safe_list("finance_snapshots")
    if any(str(row.get("recorded_at") or row.get("created_at") or "")[:10] == today for row in snapshots):
        return
    create_finance_snapshot(summary["net_worth_nok"])
