"""AGNI AI bounded local agent orchestrator with validated deliverables."""

import json
from dataclasses import dataclass, field

from loguru import logger

from app.core.llm_client import llm_client
from app.core.model_registry import classify_task, route
from app.deliverables.doc_builder import (
    build_approval_note_docx,
    build_calc_sheet_xlsx,
    build_ppt_deck,
)
from app.rag.knowledge_base import build_grounded_context
from app.tools.sandbox import cleanup_sandbox, run_python_sandboxed

MAX_STEPS = 6
NO_EVIDENCE_MARKER = "NO_RELEVANT_INTERNAL_EVIDENCE_FOUND"

SYSTEM_PROMPT = """
You are AGNI AI, a local on-premise agentic workbench.

Return exactly one JSON object per turn:
{"thought":"...","tool":"...","args":{...}}

Available tools:
- search_knowledge_base(query)
- run_python(code)
- generate_approval_note(title, ref_no, background, findings, recommendation)
- generate_presentation(title, subtitle, slides)
- generate_calc_sheet(title, headers, rows, formula_notes)
- FINISH(final_answer)

Rules:
1. Search local evidence for report, summary, approval-note, or presentation tasks.
2. Do not search again after one successful search.
3. If evidence is missing, call FINISH and do not create a file.
4. Never invent facts.
5. Presentation slides must use {"heading":"...","bullets":["..."]}.
6. Calculation rows must contain actual values, not repeated headers.
7. After one successful deliverable generation, stop immediately.
8. If a tool fails, return its actual error and do not claim success.
"""


@dataclass
class AgentStep:
    thought: str
    tool: str
    args: dict
    observation: str = ""


@dataclass
class AgentRun:
    goal: str
    routing_log: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    final_answer: str = ""
    deliverable_paths: list = field(default_factory=list)


def _extract_json(raw: str) -> dict | None:
    start = raw.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(raw)):
        char = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start:index + 1])
                except json.JSONDecodeError:
                    return None

    return None


def _no_evidence_answer(goal: str) -> str:
    return (
        "No relevant local evidence was found, so no deliverable was created. "
        "Please ingest or attach the correct local source document and run the "
        f"request again.\n\nRequested task: {goal}"
    )


def _validate_presentation(args: dict) -> str | None:
    slides = args.get("slides")
    if not isinstance(slides, list) or not slides:
        return "ERROR: presentation requires a non-empty slides list."

    for number, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            return f"ERROR: slide {number} must be an object."
        if not isinstance(slide.get("heading"), str) or not slide["heading"].strip():
            return f"ERROR: slide {number} is missing heading."
        if not isinstance(slide.get("bullets"), list):
            return f"ERROR: slide {number} bullets must be a list."
        if not all(isinstance(item, str) for item in slide["bullets"]):
            return f"ERROR: slide {number} bullets must contain strings."

    return None


def _validate_calc_sheet(args: dict) -> str | None:
    headers = args.get("headers")
    rows = args.get("rows")

    if not isinstance(headers, list) or not headers:
        return "ERROR: calculation sheet requires non-empty headers."
    if not isinstance(rows, list) or not rows:
        return "ERROR: calculation sheet requires non-empty rows."

    for number, row in enumerate(rows, start=1):
        if not isinstance(row, list):
            return f"ERROR: calculation row {number} must be a list."
        if len(row) != len(headers):
            return (
                f"ERROR: calculation row {number} has {len(row)} values, "
                f"but there are {len(headers)} headers."
            )
        if row == headers:
            return f"ERROR: calculation row {number} repeats the header row."

    return None


def _validate_tool(tool: str, args: dict) -> str | None:
    if tool == "generate_presentation":
        return _validate_presentation(args)

    if tool == "generate_calc_sheet":
        return _validate_calc_sheet(args)

    if tool == "generate_approval_note":
        required = ("title", "background", "findings", "recommendation")
        missing = [key for key in required if not args.get(key)]
        if missing:
            return f"ERROR: approval note missing: {', '.join(missing)}"

    return None


async def _dispatch(tool: str, args: dict) -> str:
    if tool == "search_knowledge_base":
        return build_grounded_context(str(args.get("query", "")))

    if tool == "run_python":
        result = await run_python_sandboxed(str(args.get("code", "")))
        if result.get("workdir"):
            cleanup_sandbox(result["workdir"])
        return json.dumps(result, default=str)[:5000]

    if tool == "generate_approval_note":
        path = build_approval_note_docx(
            title=args["title"],
            ref_no=args.get("ref_no", "AGNI/AI-DRAFT/AUTO"),
            background=args["background"],
            findings=args["findings"],
            recommendation=args["recommendation"],
        )
        return json.dumps({"deliverable_path": path})

    if tool == "generate_presentation":
        path = build_ppt_deck(
            title=args["title"],
            subtitle=args.get("subtitle", ""),
            slides=args["slides"],
        )
        return json.dumps({"deliverable_path": path})

    if tool == "generate_calc_sheet":
        path = build_calc_sheet_xlsx(
            title=args["title"],
            headers=args["headers"],
            rows=args["rows"],
            formula_notes=args.get("formula_notes"),
        )
        return json.dumps({"deliverable_path": path})

    return f"ERROR: unknown tool '{tool}'"


async def run_agent(goal: str, has_image: bool = False, image_path: str | None = None) -> AgentRun:
    run = AgentRun(goal=goal)
    signature = classify_task(goal, has_image=has_image)
    decision = route(signature)

    run.routing_log.append({
        "task_type": signature.task_type.value,
        "selected_model": decision.model.display_name,
        "model_tag": decision.model.name,
        "reason": decision.reason,
    })

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"GOAL: {goal}"
            + (f"\nATTACHED IMAGE: {image_path}" if image_path else ""),
        },
    ]

    search_completed = False

    for _ in range(MAX_STEPS):
        try:
            response = await llm_client.chat(
                model=decision.model.name,
                messages=messages,
                temperature=0.2,
            )
        except Exception as error:
            run.final_answer = f"Local model execution failed: {error}"
            break

        parsed = _extract_json(response.get("content", ""))
        if not parsed:
            run.final_answer = response.get("content", "Task could not be parsed.")
            break

        thought = parsed.get("thought", "")
        tool = parsed.get("tool", "FINISH")
        args = parsed.get("args") or {}

        if tool == "FINISH":
            run.final_answer = args.get("final_answer", "Task complete.")
            run.steps.append(AgentStep(thought, tool, args, "(loop ended)"))
            break

        if tool == "search_knowledge_base" and search_completed:
            run.final_answer = "Evidence was already retrieved; repeated search was blocked."
            run.steps.append(AgentStep(
                "Blocked repeated search.",
                "FINISH",
                {"final_answer": run.final_answer},
                "(loop ended)",
            ))
            break

        validation_error = _validate_tool(tool, args)
        if validation_error:
            run.final_answer = validation_error
            run.steps.append(AgentStep(thought, tool, args, validation_error))
            run.steps.append(AgentStep(
                "Invalid tool arguments; stopping without claiming success.",
                "FINISH",
                {"final_answer": validation_error},
                "(loop ended)",
            ))
            break

        try:
            observation = await _dispatch(tool, args)
        except Exception as error:
            observation = f"ERROR executing {tool}: {error}"

        run.steps.append(AgentStep(thought, tool, args, observation))

        if tool == "search_knowledge_base":
            if NO_EVIDENCE_MARKER in observation:
                run.final_answer = _no_evidence_answer(goal)
                run.steps.append(AgentStep(
                    "No relevant evidence; stopping before generation.",
                    "FINISH",
                    {"final_answer": run.final_answer},
                    "(loop ended)",
                ))
                break
            search_completed = True

        if observation.startswith("ERROR"):
            run.final_answer = observation
            run.steps.append(AgentStep(
                "Tool failure; reporting the actual error.",
                "FINISH",
                {"final_answer": observation},
                "(loop ended)",
            ))
            break

        if "deliverable_path" in observation:
            try:
                deliverable = json.loads(observation)["deliverable_path"]
                run.deliverable_paths.append(deliverable)
                run.final_answer = f"Created the requested deliverable: {deliverable}"
                run.steps.append(AgentStep(
                    "Deliverable created; stopping immediately.",
                    "FINISH",
                    {"final_answer": run.final_answer},
                    "(loop ended)",
                ))
                break
            except (KeyError, json.JSONDecodeError):
                logger.warning("Could not register generated deliverable")

        messages.append({"role": "assistant", "content": json.dumps(parsed)})
        messages.append({
            "role": "user",
            "content": (
                f"OBSERVATION from {tool}: {observation}\n"
                "Continue only with the next required action."
            ),
        })
    else:
        run.final_answer = "The task stopped at the safety step limit."

    return run
