from fastapi import APIRouter, Depends

from app.core.model_registry import (
    MODEL_REGISTRY,
    classify_task,
    route,
)
from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/models",
    tags=["models"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/registry")
async def get_registry():
    return {
        key: {
            "display_name": spec.display_name,
            "params": spec.params,
            "good_at": [
                task.value
                for task in spec.good_at
            ],
            "supports_vision": spec.supports_vision,
            "context_window": spec.context_window,
            "relative_speed": spec.relative_speed,
            "notes": spec.notes,
        }
        for key, spec in MODEL_REGISTRY.items()
    }


@router.get("/preview-routing")
async def preview_routing(text: str):
    signal = classify_task(text)
    decision = route(signal)

    return {
        "detected_task_type": signal.task_type.value,
        "selected_model": decision.model.display_name,
        "reason": decision.reason,
    }