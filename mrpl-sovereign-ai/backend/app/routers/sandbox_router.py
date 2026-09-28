from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.tools.sandbox import (
    cleanup_sandbox,
    run_python_sandboxed,
)


router = APIRouter(
    prefix="/api/sandbox",
    tags=["sandbox"],
    dependencies=[Depends(get_current_user)],
)


class CodeRequest(BaseModel):
    code: str


@router.post("/run")
async def run_code(payload: CodeRequest):
    result = await run_python_sandboxed(payload.code)

    workdir = result.get("workdir")

    if workdir:
        cleanup_sandbox(workdir)
        result.pop("workdir", None)

    return result
