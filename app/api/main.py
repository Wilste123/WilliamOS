import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import attach_refreshed_token_headers
from app.api.routes import assets, auth, chat, documents, goals, memory, projects, tasks
from app.api.routes.decisions import router as decisions_router
from app.api.routes.events import router as events_router
from app.api.routes.inbox import router as inbox_router
from app.api.routes.overview import router as overview_router
from app.api.routes.usage import router as usage_router

app = FastAPI(
    title="WilliamOS API",
    version="0.2.0",
    description="Public API for WilliamOS clients (Next.js, mobile, voice).",
    redirect_slashes=False,
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Access-Token", "X-Refresh-Token"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(overview_router, tags=["overview"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(goals.router, prefix="/goals", tags=["goals"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(usage_router, prefix="/usage", tags=["usage"])

logger = logging.getLogger(__name__)


@app.middleware("http")
async def refreshed_token_middleware(request: Request, call_next):
    response = await call_next(request)
    return attach_refreshed_token_headers(response)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled API error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error"},
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": "WilliamOS"}


@app.get("/")
def root():
    return {
        "app": "WilliamOS",
        "status": "running",
        "docs": "/docs",
        "modules": ["auth", "inbox", "dashboard", "tasks", "projects", "assets", "documents", "decisions", "timeline", "chat"],
    }
