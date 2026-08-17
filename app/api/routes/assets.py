from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.models.asset import AssetCreate, AssetUpdate
from app.services.action_engine import create_asset as create_asset_record, update_asset
from app.services.storage_service import list_records

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def list_assets():
    return list_records("assets")


@router.post("")
def create_asset(asset: AssetCreate):
    return create_asset_record(asset.model_dump(mode="json"))


@router.patch("/{asset_id}")
def patch_asset(asset_id: str, updates: AssetUpdate):
    asset = update_asset(asset_id, updates.model_dump(mode="json", exclude_none=True))
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
