from fastapi import Depends, FastAPI

from app.api.dependencies import require_authenticated_user
from app.api.routes import assets, chat, documents, projects, tasks
from app.api.routes.auth import router as auth_router
from app.api.routes.decisions import router as decisions_router
from app.api.routes.events import router as events_router
from app.api.routes.inbox import router as inbox_router
from app.api.routes.overview import router as overview_router

app = FastAPI(title="WilliamOS API", version="0.1.0")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
protected = [Depends(require_authenticated_user)]

app.include_router(chat.router, prefix="/chat", tags=["chat"], dependencies=protected)
app.include_router(inbox_router, prefix="/inbox", tags=["inbox"], dependencies=protected)
app.include_router(overview_router, tags=["overview"], dependencies=protected)
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"], dependencies=protected)
app.include_router(projects.router, prefix="/projects", tags=["projects"], dependencies=protected)
app.include_router(assets.router, prefix="/assets", tags=["assets"], dependencies=protected)
app.include_router(documents.router, prefix="/documents", tags=["documents"], dependencies=protected)
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"], dependencies=protected)
app.include_router(events_router, prefix="/events", tags=["events"], dependencies=protected)


@app.get("/")
def root():
    return {
        "app": "WilliamOS",
        "status": "running",
        "modules": ["inbox", "dashboard", "tasks", "projects", "assets", "documents", "decisions", "timeline"],
    }
