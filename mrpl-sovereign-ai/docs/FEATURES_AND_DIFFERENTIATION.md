# Feature List and Differentiation

## Every feature, and why it exists

| # | Feature | What it does | Why it matters for MRPL |
|---|---|---|---|
| 1 | Pluggable model registry | One dataclass entry per model; router re-scores automatically | New open-weight model drops in without touching orchestration code |
| 2 | Rule-based + LLM-fallback classifier | Cheap keyword pass first, escalates to fast model only when ambiguous | Near-zero latency for obvious cases |
| 3 | ReAct-style agent loop | Plan → tool call → observe → reflect → repeat, bounded at 6 steps | The actual difference between a chatbot and an agent |
| 4 | Sandboxed code execution | Subprocess with CPU/time/memory limits, wiped temp dir, no network | Lets the agent run and self-correct calculations safely |
| 5 | File read/write with allow-listing | Every path resolved and checked before I/O | Prevents a hallucinating model from touching arbitrary paths |
| 6 | Local RAG knowledge base | Chroma (embedded) + sentence-transformers, chunked ingestion | Answers grounded in the org's SOPs/manuals, with source shown |
| 7 | On-device OCR + vision pipeline | Tesseract + local VLM for handwriting, P&ID symbols, tables | Handles the "scanned drawings and inspection reports" scenario |
| 8 | Real deliverable generation | python-docx / python-pptx / openpyxl builders | Directly answers "real deliverables, not just chat replies" |
| 9 | Network Sentinel | psutil-based live egress monitor, LOCAL/PRIVATE_LAN/EXTERNAL | The literal sovereignty proof the brief asks jurors to see |
| 10 | Hard-pinned local-only LLM client | Refuses to start if inference URL isn't loopback/private-LAN | Structural guarantee, not a policy statement |
| 11 | Clean multi-page UI | Agent Workbench, Model Registry, Knowledge Base, Sandbox, Deliverables, live Network Sentinel | Makes every backend capability visible and demoable |

## Why this stands apart

- **Cloud assistants are structurally disqualified**, not just discouraged —
  this system has no code path capable of sending data externally, and it
  proves that live rather than asserting it.
- **Generic local chat UIs give you one model and one chat box.** They don't
  route between models by task, don't call tools, don't touch a knowledge
  base, and don't produce Office deliverables.
- **Most agent-framework demos are impressive in a notebook and useless on a
  factory floor** because they don't produce something a reviewing engineer
  can actually file. Every run here ends in a real downloadable file.
- **The model-agnostic registry future-proofs the deployment** — swapping in
  the next Qwen/DeepSeek/GLM release is one dictionary entry, not a rewrite.

## Honest limitations to state to judges

- The agent loop is bounded (6 steps) for predictable demos; production needs
  per-task budgets and human-in-the-loop approval gates. Every generated Word
  note is explicitly labeled a draft.
- Windows lacks POSIX `resource` limits for the sandbox; run under WSL2 for a
  hard guarantee in production.
- Vision-model accuracy on dense P&ID symbol sets depends on the chosen VLM;
  plan a small fine-tuning/eval pass on MRPL's actual drawing conventions.
