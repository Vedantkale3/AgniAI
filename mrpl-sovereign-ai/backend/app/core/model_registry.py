"""
MODEL REGISTRY + AUTO-ROUTER
=============================
This is the heart of the "not locked to one model" requirement.

Design:
- Every model is registered with a capability profile (task types it is
  good at, context window, relative speed, modality support).
- A TaskProfiler inspects the incoming request (text heuristics + optional
  cheap classifier pass on the small-fast model) and produces a TaskSignature.
- The Router scores every registered model against the TaskSignature and
  picks the best match. Ties broken by speed.
- Adding a new model = adding one ModelSpec entry. Nothing else in the
  codebase changes. This satisfies the "addable later without redesign"
  requirement directly.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from app.config import settings


class TaskType(str, Enum):
    CODE_GEN = "code_gen"
    CODE_DEBUG = "code_debug"
    DOCUMENT_SUMMARY = "document_summary"
    APPROVAL_NOTE = "approval_note"
    VISION_OCR = "vision_ocr"
    ENGINEERING_CALC = "engineering_calc"
    LONG_REASONING = "long_reasoning"
    GENERAL_CHAT = "general_chat"
    SPREADSHEET = "spreadsheet"


@dataclass
class ModelSpec:
    name: str                 # tag used by local runtime (ollama/vllm)
    display_name: str
    good_at: list             # list[TaskType]
    supports_vision: bool = False
    context_window: int = 32768
    relative_speed: int = 5   # 1 (slow/heavy) - 10 (fast/light)
    quantization: str = "Q4_K_M"
    params: str = "unknown"
    notes: str = ""


# ---------------------------------------------------------------------------
# REGISTRY: add a new open-weight model by appending one entry here.
# Nothing downstream needs to change - the router re-scores automatically.
# ---------------------------------------------------------------------------
MODEL_REGISTRY: dict[str, ModelSpec] = {
    "coder": ModelSpec(
        name=settings.model_code,
        display_name="Qwen2.5-Coder-7B",
        good_at=[TaskType.CODE_GEN, TaskType.CODE_DEBUG, TaskType.SPREADSHEET],
        supports_vision=False,
        context_window=32768,
        relative_speed=5,
        params="7B",
        notes="Best-in-class open-weight coding model in this weight class. "
              "Used for sandboxed code generation/execution tasks.",
    ),
    "reasoner": ModelSpec(
        name=settings.model_reasoning,
        display_name="DeepSeek-R1-Distill-7B",
        good_at=[TaskType.LONG_REASONING, TaskType.ENGINEERING_CALC],
        supports_vision=False,
        context_window=16384,
        relative_speed=3,
        params="7B",
        notes="Reserved for difficult multi-step reasoning and engineering analysis.",
    ),

    "general": ModelSpec(
        name=settings.model_general,
        display_name="Qwen2.5-7B-Instruct",
        good_at=[
            TaskType.DOCUMENT_SUMMARY,
            TaskType.GENERAL_CHAT,
            TaskType.APPROVAL_NOTE,
        ],
        supports_vision=False,
        context_window=32768,
        relative_speed=8,
        params="7B",
        notes="Fast local drafting model for approval notes, summaries, presentations, and grounded Q&A.",
    ),
    "vision": ModelSpec(
        name=settings.model_vision,
        display_name="Qwen2.5-VL-7B",
        good_at=[TaskType.VISION_OCR],
        supports_vision=True,
        context_window=32768,
        relative_speed=7,
        params="7B",
        notes="Handles scanned P&IDs, handwritten inspection notes, "
              "photographs of equipment/nameplates.",
    ),
    "fast": ModelSpec(
        name=settings.model_small_fast,
        display_name="Phi-3-3.8B",
        good_at=[TaskType.GENERAL_CHAT, TaskType.DOCUMENT_SUMMARY],
        supports_vision=False,
        context_window=16384,
        relative_speed=10,
        params="3.8B",
        notes="Low-latency fallback for small workstations / venues without "
              "a 120B-class GPU, and used as the cheap task-classifier pass.",
    ),
}


@dataclass
class TaskSignature:
    task_type: TaskType
    needs_vision: bool = False
    context_hint_tokens: int = 2000
    priority: str = "quality"  # "quality" | "speed"


@dataclass
class RoutingDecision:
    model_key: str
    model: ModelSpec
    reason: str


def score_model(spec: ModelSpec, sig: TaskSignature) -> float:
    score = 0.0
    if sig.task_type in spec.good_at:
        score += 10.0
    if sig.needs_vision and not spec.supports_vision:
        return -999.0
    if sig.needs_vision and spec.supports_vision:
        score += 5.0
    if sig.context_hint_tokens > spec.context_window:
        score -= 20.0
    if sig.priority == "speed":
        score += spec.relative_speed * 0.5
    else:
        score += (10 - spec.relative_speed) * 0.2
    return score


def route(sig: TaskSignature) -> RoutingDecision:
    best_key, best_spec, best_score = None, None, float("-inf")
    for key, spec in MODEL_REGISTRY.items():
        s = score_model(spec, sig)
        if s > best_score:
            best_key, best_spec, best_score = key, spec, s

    if best_key is None or best_score < -100:
        best_key = "fast"
        best_spec = MODEL_REGISTRY["fast"]

    reason = (
        f"Task={sig.task_type.value}, vision_required={sig.needs_vision} -> "
        f"selected '{best_spec.display_name}' (score={best_score:.1f}) "
        f"because it lists {sig.task_type.value} in good_at "
        if sig.task_type in best_spec.good_at
        else f"Task={sig.task_type.value} -> fallback to '{best_spec.display_name}'"
    )
    return RoutingDecision(model_key=best_key, model=best_spec, reason=reason)


def classify_task(user_text: str, has_image: bool = False, has_code_block: bool = False) -> TaskSignature:
    """
    Lightweight rule-based classifier (Stage 1 - zero LLM cost).
    In production this is backed up by an optional Stage 2 LLM classification
    call on the 'fast' model when the rule-based pass is ambiguous - see
    app/agents/orchestrator.py::classify_with_fallback().
    """
    text = user_text.lower()

    if has_image:
        return TaskSignature(task_type=TaskType.VISION_OCR, needs_vision=True)

    code_markers = ["def ", "function ", "import ", "class ", "```", "traceback",
                     "error:", "bug", "compile", "syntax error", "fix this code"]
    if has_code_block or any(m in text for m in code_markers):
        return TaskSignature(task_type=TaskType.CODE_GEN, context_hint_tokens=4000)

    calc_markers = [
        "calculate",
        "flow rate",
        "pressure drop",
        "heat balance",
        "stoichiometry",
        "psv sizing",
        "pump head",
        "npsh",
    ]

    code_execution_markers = [
        "write and run",
        "run a python",
        "python script",
        "run code",
        "execute code",
        "sandbox",
        "excel calculation sheet",
        "xlsx",
    ]

    if any(marker in text for marker in code_execution_markers):
        return TaskSignature(
            task_type=TaskType.CODE_GEN,
            context_hint_tokens=3000,
            priority="speed",
        )

    if any(marker in text for marker in calc_markers):
        return TaskSignature(
            task_type=TaskType.ENGINEERING_CALC,
            priority="speed",
        )

    approval_markers = ["approval note", "draft a note", "recommend approval",
                         "put up a note", "for approval", "note for approval"]
    if any(m in text for m in approval_markers):
        return TaskSignature(task_type=TaskType.APPROVAL_NOTE, priority="quality")

    summary_markers = ["summarize", "summary", "key findings", "extract findings",
                        "brief me", "tl;dr"]
    if any(m in text for m in summary_markers):
        return TaskSignature(task_type=TaskType.DOCUMENT_SUMMARY)

    sheet_markers = ["excel", "spreadsheet", "xlsx", "pivot table", "column"]
    if any(m in text for m in sheet_markers):
        return TaskSignature(task_type=TaskType.SPREADSHEET)

    return TaskSignature(task_type=TaskType.GENERAL_CHAT, priority="speed")
