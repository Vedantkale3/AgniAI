# Detailed Setup Guide

## Prerequisites

- Windows 10/11 with PowerShell, or Linux
- Python 3.10+
- Node.js 18+
- A GPU with at least 16 GB VRAM for the 32B-class default registry (8 GB is
  enough if you swap to 7B/14B model tags — see README hardware notes)
- [Ollama](https://ollama.com) as the local model runtime
- Tesseract OCR binary installed and on PATH
- Poppler (for `pdf2image`)

## Step-by-step

1. Run the setup script for your OS (`setup_windows.ps1` or `setup_linux.sh`).
2. Pull the models via Ollama (see README hardware notes for smaller tags).
3. Configure `backend/.env` — copied automatically from `.env.example`.
4. Start the backend: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
5. Start the frontend: `npm run dev`, open `http://localhost:5173`.
6. Ingest a few SOPs/manuals via the Knowledge Base tab before your demo.

## Troubleshooting

- **Router always picks the same model** — check `ollama list` has all five tags.
- **OCR returns empty text** — verify `tesseract --version` runs from the shell
  launching uvicorn; add Tesseract's install dir to PATH on Windows.
- **Sandbox `resource` import fails on Windows** — `resource` is POSIX-only;
  the code already skips rlimits on Windows (`os.name != "nt"` guard), relying
  on the asyncio timeout alone. For a hard guarantee, run backend under WSL2.
- **Network Sentinel shows EXTERNAL unexpectedly** — usually another process
  on the same machine; re-check after closing background apps.
