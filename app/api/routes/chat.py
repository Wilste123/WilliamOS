import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.pa_agent import ask_agent, ask_agent_stream
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


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/")
def chat(request: ChatRequest):
    answer, sources = ask_agent(
        request.message,
        use_documents=request.use_documents,
        history=request.history or None,
    )
    return {"answer": answer, "sources": sources}


@router.post("/stream")
def chat_stream(request: ChatRequest):
    def generate():
        try:
            for event in ask_agent_stream(
                request.message,
                use_documents=request.use_documents,
                history=request.history or None,
            ):
                yield _sse(event)
        except Exception as exc:
            yield _sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/memory")
def remember(request: MemoryRequest):
    return save_memory(request.value, request.key, request.category)


@router.get("/self-evolve")
def self_evolve_status():
    return analyze_requests()
