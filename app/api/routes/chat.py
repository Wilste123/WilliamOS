from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.pa_agent import ask_agent
from app.services.action_engine import build_dashboard_summary, build_timeline, capture_inbox_entry
from app.services.memory_service import save_memory
from app.agents.self_evolve import analyze_requests_locally

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class MemoryRequest(BaseModel):
    value: str
    key: str | None = None
    category: str | None = None


class InboxRequest(BaseModel):
    text: str


@router.post("/")
def chat(request: ChatRequest):
    answer = ask_agent(request.message)
    return {"answer": answer}


@router.post("/memory")
def remember(request: MemoryRequest):
    return save_memory(request.value, request.key, request.category)


@router.get("/self-evolve")
def self_evolve_status():
    return analyze_requests_locally()


@router.post("/inbox")
def capture_inbox(request: InboxRequest):
    return capture_inbox_entry(request.text)


@router.get("/dashboard")
def dashboard():
    return build_dashboard_summary()


@router.get("/timeline")
def timeline():
    return build_timeline()
