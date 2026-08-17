"""Track daily app opens for the 7-day validation milestone."""

from datetime import date, datetime, timedelta, timezone

from app.services.storage_service import create_record, list_records


def _today() -> date:
    return datetime.now(timezone.utc).date()


def record_app_open() -> dict:
    today = _today().isoformat()
    opens = list_records("usage_log")
    if not any(entry.get("opened_on") == today for entry in opens):
        create_record("usage_log", {"opened_on": today})
    return get_usage_stats()


def get_usage_stats() -> dict:
    opens = sorted(
        {entry.get("opened_on") for entry in list_records("usage_log") if entry.get("opened_on")}
    )
    open_dates = [date.fromisoformat(value) for value in opens]
    today = _today()
    week_start = today - timedelta(days=today.weekday())
    days_this_week = sum(1 for opened in open_dates if opened >= week_start)

    streak = 0
    cursor = today
    open_set = set(open_dates)
    while cursor in open_set:
        streak += 1
        cursor -= timedelta(days=1)

    last_opened = max(open_dates).isoformat() if open_dates else None
    return {
        "days_opened_this_week": days_this_week,
        "total_opens": len(open_dates),
        "streak_days": streak,
        "last_opened_at": last_opened,
        "seven_day_goal_met": len(open_dates) >= 7,
    }
