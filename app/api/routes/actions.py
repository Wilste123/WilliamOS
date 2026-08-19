from pydantic import BaseModel, Field

from app.api.deps import protected_router
from app.services.chat_actions import execute_and_finalize

router = protected_router()


class ExecuteActionRequest(BaseModel):
    action: dict


class ExecuteBatchRequest(BaseModel):
    actions: list[dict] = Field(default_factory=list)


@router.post("/execute")
def execute_action(request: ExecuteActionRequest):
    outcome = execute_and_finalize(request.action)
    return outcome


@router.post("/execute-batch")
def execute_actions_batch(request: ExecuteBatchRequest):
    results = [execute_and_finalize(action) for action in request.actions]
    ok_count = sum(1 for row in results if row.get("ok"))
    return {"results": results, "executed": ok_count, "total": len(results)}
