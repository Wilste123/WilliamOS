"""Health metrics — manual entry + integration-ready sources."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.action_engine import append_event
from app.services.storage_service import create_record, list_records, update_record

METRIC_UNITS = {
    "weight": "kg",
    "sleep_hours": "t",
    "activity_minutes": "min",
    "steps": "steg",
}


def _safe_list() -> list[dict]:
    try:
        return list_records("health_metrics")
    except Exception:
        return []


def _latest_metric(metrics: list[dict], metric_type: str) -> dict | None:
    filtered = [row for row in metrics if row.get("metric_type") == metric_type]
    if not filtered:
        return None
    return max(filtered, key=lambda row: row.get("recorded_at") or row.get("created_at") or "")


def _avg_metric(metrics: list[dict], metric_type: str, days: int = 7) -> float | None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    values: list[float] = []
    for row in metrics:
        if row.get("metric_type") != metric_type:
            continue
        raw = row.get("recorded_at") or row.get("created_at")
        if not raw:
            continue
        try:
            recorded = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            continue
        if recorded >= cutoff:
            values.append(float(row.get("value") or 0))
    if not values:
        return None
    return sum(values) / len(values)


def build_health_summary() -> dict:
    metrics = _safe_list()
    weight = _latest_metric(metrics, "weight")
    sleep = _avg_metric(metrics, "sleep_hours", days=7)
    activity = _avg_metric(metrics, "activity_minutes", days=7)
    steps = _avg_metric(metrics, "steps", days=7)

    weight_goals = []
    try:
        from app.services.storage_service import list_records as lr

        weight_goals = [
            goal
            for goal in lr("goals")
            if goal.get("status") in {"active", "open", "in_progress"}
            and "kg" in (goal.get("title") or "").lower()
        ]
    except Exception:
        pass

    return {
        "latest_weight_kg": float(weight["value"]) if weight else None,
        "latest_weight_at": weight.get("recorded_at") if weight else None,
        "avg_sleep_hours_7d": round(sleep, 1) if sleep is not None else None,
        "avg_activity_minutes_7d": round(activity, 0) if activity is not None else None,
        "avg_steps_7d": round(steps, 0) if steps is not None else None,
        "weight_goal": weight_goals[0] if weight_goals else None,
        "recent_metrics": sorted(
            metrics,
            key=lambda row: row.get("recorded_at") or row.get("created_at") or "",
            reverse=True,
        )[:10],
        "sources": sorted({row.get("source") or "manual" for row in metrics}),
    }


def create_health_metric(payload: dict) -> dict:
    metric_type = payload.get("metric_type")
    if metric_type in METRIC_UNITS and not payload.get("unit"):
        payload = {**payload, "unit": METRIC_UNITS[metric_type]}
    metric = create_record("health_metrics", payload)
    append_event(
        title=f"Helse registrert: {metric_type} = {metric.get('value')}",
        event_type="health_metric_created",
        notes=f"Kilde: {metric.get('source', 'manual')}",
        visibility="private",
    )
    return metric


def update_health_metric(metric_id: str, updates: dict) -> dict | None:
    return update_record("health_metrics", metric_id, updates)
