from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel

from app.agents.orchestrator import run_agent
from app.config import settings
from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
    dependencies=[Depends(get_current_user)],
)


class GoalRequest(BaseModel):
    goal: str


def serialize_run(run):
    return {
        "goal": run.goal,
        "routing_log": run.routing_log,
        "steps": [
            {
                "thought": step.thought,
                "tool": step.tool,
                "args": step.args,
                "observation": step.observation,
            }
            for step in run.steps
        ],
        "final_answer": run.final_answer,
        "deliverable_paths": run.deliverable_paths,
    }


@router.post("/run")
async def agent_run(payload: GoalRequest):
    run = await run_agent(payload.goal)
    return serialize_run(run)


@router.post("/run-with-image")
async def agent_run_with_image(
        goal: str = Form(...),
        file: UploadFile = File(...),
):
    extension = Path(file.filename or "").suffix
    save_path = (
            Path(settings.upload_dir)
            / f"{uuid.uuid4().hex}{extension}"
    )

    save_path.write_bytes(await file.read())

    run = await run_agent(
        goal,
        has_image=True,
        image_path=str(save_path),
    )

    return serialize_run(run)