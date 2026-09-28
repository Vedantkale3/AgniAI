# MRPL Sovereign Agentic AI Workbench

An air-gapped, multi-model, agentic AI system for confidential industrial work —
built for the MRPL "Smart Automation" problem statement.

## What this actually is

1. A **model router** that auto-picks the right open-weight model per task
   (coding vs. reasoning vs. vision vs. quick chat) from a pluggable registry.
2. An **agent loop** that plans multi-step work, calls local tools (sandboxed
   code execution, file I/O, knowledge base search, document generation),
   observes results, and iterates instead of answering once.
3. A **local RAG knowledge base** grounded in your own SOPs/manuals/correspondence,
   embedded and searched entirely on-device via Chroma + sentence-transformers.
4. An **on-device vision/OCR pipeline** (Tesseract + a local VLM) for scanned
   inspection reports, handwritten notes, and P&ID excerpts.
5. A **real deliverable generator** — Word approval notes, PowerPoint decks,
   Excel calculation sheets — not just chat text.
6. A **Network Sentinel** that proves, live, that zero packets leave the box.

## Architecture

```
frontend/  (React + Vite)          backend/  (FastAPI)
  ChatWorkbench ─────────────────▶  /api/agent/run        → orchestrator.run_agent()
  ModelRegistryPage ─────────────▶  /api/models/registry  → model_registry.py
  KnowledgeBasePage ─────────────▶  /api/knowledge/*       → rag/knowledge_base.py
  SandboxPage ───────────────────▶  /api/sandbox/run       → tools/sandbox.py
  NetworkMonitor (right rail) ───▶  /api/network/status    → tools/net_sentinel.py
  DeliverablesPage ──────────────▶  /api/deliverables/*    → deliverables/doc_builder.py

  All backend inference calls go through core/llm_client.py, which is hard-pinned
  to a loopback/private-LAN base_url and refuses to start otherwise.
```

## Quick Start (Windows / PowerShell)

```powershell
.\setup_windows.ps1
```

Then follow the printed next steps. Full details in `docs/SETUP_GUIDE.md`.

## Quick Start (Linux)

```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

## Hardware notes

Default registry uses 32B-class models (coder/reasoner/general) + a 7B vision
model + a 14B fast fallback — runs on a single RTX 4090 / A6000 class GPU at
4-bit quantization. For a laptop demo, swap every tag in `backend/.env` to the
`:7b` or `:14b` variants of the same model families; the router code needs
zero changes.

## Demo script (for judges)

1. Open Model Registry tab — show the pluggable model list, explain hot-swap.
2. Ask the agent to summarize an attached scanned inspection report and draft
   an approval note. Watch it route to the vision model, extract findings,
   hand off to the reasoning model, and produce a downloadable .docx.
3. Ask it to write and run a Python calculation. Watch it route to the coder
   model, execute in the sandbox tab, show real stdout.
4. Point at the Network Sentinel panel throughout — it never leaves SEALED.
5. Show Knowledge Base tab — ingest an SOP, ask a grounded question, show the
   cited source.

See `docs/FEATURES_AND_DIFFERENTIATION.md` for the full feature list and
`docs/ARCHITECTURE.md` for the request lifecycle deep-dive.
