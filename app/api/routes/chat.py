import json

from fastapi import Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.agents.pa_agent import ask_agent, ask_agent_stream
from app.api.deps import CurrentUser, protected_router, use_user_context
from app.services.chat_history_service import (
    append_chat_messages,
    clear_chat_messages,
    list_chat_messages,
)
from app.services.memory_service import save_memory
from app.agents.self_evolve import analyze_requests

router = protected_router()


class ChatRequest(BaseModel):
    message: str
    use_documents: bool = True
    history: list[dict] = []
    document_id: str | None = None


class MemoryRequest(BaseModel):
    value: str
    key: str | None = None
    category: str | None = None


class ChatHistoryAppendRequest(BaseModel):
    messages: list[dict] = Field(default_factory=list)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("")
def chat(request: ChatRequest, user: CurrentUser):
    use_user_context(user)
    answer, sources = ask_agent(
        request.message,
        use_documents=request.use_documents,
        history=request.history or None,
        document_id=request.document_id,
        user_context=user,
    )
    return {"answer": answer, "sources": sources}


@router.post("/stream")
async def chat_stream(request: ChatRequest, user: CurrentUser):
    async def generate():
        use_user_context(user)
        try:
            for event in ask_agent_stream(
                request.message,
                use_documents=request.use_documents,
                history=request.history or None,
                document_id=request.document_id,
                user_context=user,
            ):
                use_user_context(user)
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


@router.get("/history")
def chat_history(limit: int = Query(40, ge=1, le=100)):
    return {"messages": list_chat_messages(limit)}


@router.post("/history")
def save_chat_history(request: ChatHistoryAppendRequest):
    saved = append_chat_messages(request.messages)
    return {"saved": saved}


@router.delete("/history")
def delete_chat_history():
    clear_chat_messages()
    return {"cleared": True}
