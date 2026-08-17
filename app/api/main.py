import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import assets, auth, chat, documents, memory, projects, tasks
from app.api.routes.decisions import router as decisions_router
from app.api.routes.events import router as events_router
from app.api.routes.inbox import router as inbox_router
from app.api.routes.overview import router as overview_router

app = FastAPI(
    title="WilliamOS API",
    version="0.2.0",
    description="Public API for WilliamOS clients (Next.js, mobile, voice).",
    redirect_slashes=False,
)

_cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"])
app.include_router(overview_router, tags=["overview"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
app.include_router(events_router, prefix="/events", tags=["events"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])


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
