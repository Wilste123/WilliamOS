from fastapi import FastAPI

from app.api.routes import assets, chat, documents, projects, tasks
from app.api.routes.decisions import router as decisions_router
from app.api.routes.events import router as events_router

app = FastAPI(title="WilliamOS API", version="0.1.0")

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
app.include_router(events_router, prefix="/events", tags=["events"])


@app.get("/")
def root():
    return {
        "app": "WilliamOS",
        "status": "running",
        "modules": ["inbox", "dashboard", "tasks", "projects", "assets", "documents", "decisions", "timeline"],
    }
