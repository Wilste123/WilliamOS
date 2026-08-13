from fastapi import FastAPI
from app.api.routes import chat, tasks, projects, assets, documents

app = FastAPI(title="WilliamOS API", version="0.1.0")

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(assets.router, prefix="/assets", tags=["assets"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])


@app.get("/")
def root():
    return {"app": "WilliamOS", "status": "running"}
