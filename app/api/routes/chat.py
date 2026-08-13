from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.pa_agent import ask_agent
from app.services.memory_service import save_memory
from app.agents.self_evolve import analyze_requests_locally

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    use_documents: bool = True


class MemoryRequest(BaseModel):
    value: str
    key: str | None = None
    category: str | None = None


@router.post("/")
def chat(request: ChatRequest):
    answer, sources = ask_agent(request.message, use_documents=request.use_documents)
    return {"answer": answer, "sources": sources}


@router.post("/memory")
def remember(request: MemoryRequest):
    return save_memory(request.value, request.key, request.category)


@router.get("/self-evolve")
def self_evolve_status():
    return analyze_requests_locally()
