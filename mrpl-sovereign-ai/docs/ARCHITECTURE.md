# Architecture Deep-Dive

## Request lifecycle for an agent run

1. User submits a goal (text, optionally + image/PDF) via `ChatWorkbench.jsx`.
2. `POST /api/agent/run` or `/api/agent/run-with-image` hits `orchestrator.run_agent()`.
3. `classify_with_fallback()` runs Stage-1 rule-based classification; escalates
   to a cheap Stage-2 LLM call on the `fast` model if ambiguous and long.
4. `model_registry.route()` scores every `ModelSpec` against the resulting
   `TaskSignature` and returns a `RoutingDecision`.
5. The orchestrator enters the ReAct loop: sends system prompt + goal to the
   selected model, parses a JSON `{thought, tool, args}` step, dispatches the
   tool, appends the observation, repeats until `FINISH` or `MAX_STEPS`.
6. Tool calls hit: `rag/knowledge_base.py`, `tools/sandbox.py`,
   `tools/file_tools.py`, `deliverables/doc_builder.py`, `vision/ocr_vision.py`.
7. The full run (routing log, every step + observation, final answer,
   deliverable paths) returns to the frontend and renders step-by-step.

## Why JSON-structured steps instead of native function calling

Native OpenAI-style function calling depends on the local runtime's specific
support and schema quirks (varies by Ollama model). A plain JSON contract in
the system prompt keeps this portable across any OpenAI-compatible local
server, and makes debugging trivial during a live demo.

## Extending the registry

```python
MODEL_REGISTRY["new_coder"] = ModelSpec(
    name="new-model-tag:size",
    display_name="New Model Display Name",
    good_at=[TaskType.CODE_GEN, TaskType.CODE_DEBUG],
    supports_vision=False,
    context_window=131072,
    relative_speed=6,
    params="14B",
    notes="Why this model earns a slot.",
)
```

Nothing else changes — router, UI, and agent loop all iterate `MODEL_REGISTRY`.

## Security posture summary

- No cloud LLM API keys anywhere in the codebase.
- `LocalLLMClient` refuses to initialize against a non-loopback/non-LAN URL.
- File tools validate every path against an allow-list before I/O.
- Sandbox execution has no network access path and is resource-bounded.
- CORS restricted to known local frontend origins, not wildcarded.
- Network Sentinel is a continuously-polled runtime proof, not a checkbox.
