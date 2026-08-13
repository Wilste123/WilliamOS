from fastapi import APIRouter, HTTPException

from app.models.asset import AssetCreate
from app.services.action_engine import create_asset as create_asset_record, update_asset
from app.services.storage_service import list_records

router = APIRouter()


@router.get("/")
def list_assets():
    return list_records("assets")


@router.post("/")
def create_asset(asset: AssetCreate):
    return create_asset_record(asset.model_dump(mode="json"))


@router.patch("/{asset_id}")
def patch_asset(asset_id: str, updates: dict):
    asset = update_asset(asset_id, updates)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
