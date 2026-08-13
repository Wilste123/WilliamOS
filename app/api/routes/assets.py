from fastapi import APIRouter
from uuid import uuid4
from app.models.asset import AssetCreate
from app.database.supabase import get_supabase

router = APIRouter()
LOCAL_ASSETS = []


@router.get("/")
def list_assets():
    supabase = get_supabase()
    if supabase is None:
        return LOCAL_ASSETS
    return supabase.table("assets").select("*").order("created_at", desc=True).execute().data


@router.post("/")
def create_asset(asset: AssetCreate):
    supabase = get_supabase()
    payload = asset.model_dump(mode="json")
    if supabase is None:
        payload["id"] = str(uuid4())
        LOCAL_ASSETS.append(payload)
        return payload
    return supabase.table("assets").insert(payload).execute().data
