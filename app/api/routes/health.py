from fastapi import HTTPException

from app.api.deps import protected_router
from app.models.health import HealthMetricCreate, HealthMetricUpdate
from app.services.health_service import build_health_summary, create_health_metric, update_health_metric
from app.services.storage_service import list_records

router = protected_router()


@router.get("/summary")
def health_summary():
    return build_health_summary()


@router.get("/metrics")
def list_metrics():
    return list_records("health_metrics")


@router.post("/metrics")
def create_metric(metric: HealthMetricCreate):
    try:
        return create_health_metric(metric.model_dump(mode="json"))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/metrics/{metric_id}")
def patch_metric(metric_id: str, updates: HealthMetricUpdate):
    metric = update_health_metric(metric_id, updates.model_dump(mode="json", exclude_none=True))
    if metric is None:
        raise HTTPException(status_code=404, detail="Metric not found")
    return metric
