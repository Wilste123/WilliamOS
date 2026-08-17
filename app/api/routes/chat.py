from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.agents.pa_agent import ask_agent
from app.api.deps import get_current_user
from app.services.memory_service import save_memory
from app.agents.self_evolve import analyze_requests

router = APIRouter(dependencies=[Depends(get_current_user)])


class ChatRequest(BaseModel):
    message: str
    use_documents: bool = True
    history: list[dict] = []


class MemoryRequest(BaseModel):
    value: str
    key: str | None = None
    category: str | None = None


@router.post("/")
def chat(request: ChatRequest):
    answer, sources = ask_agent(
        request.message,
        use_documents=request.use_documents,
        history=request.history or None,
    )
    return {"answer": answer, "sources": sources}


@router.post("/memory")
def remember(request: MemoryRequest):
    return save_memory(request.value, request.key, request.category)


@router.get("/self-evolve")
def self_evolve_status():
    return analyze_requests()
