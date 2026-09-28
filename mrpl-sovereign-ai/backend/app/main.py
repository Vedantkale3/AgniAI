"""
MRPL SOVEREIGN AGENTIC AI WORKBENCH - FastAPI entrypoint.

Run with:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.routers import (
    auth,
    chat,
    deliverables_router,
    knowledge,
    models,
    network_monitor,
    sandbox_router,
)


app = FastAPI(
    title="MRPL Sovereign Agentic AI Workbench",
    description=(
        "Air-gapped, multi-model, agentic AI "
        "for confidential industrial work."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication remains public so users can obtain their first token.
app.include_router(auth.router)

# All feature routers require a valid Bearer token.
app.include_router(chat.router)
app.include_router(knowledge.router)
app.include_router(models.router)
app.include_router(sandbox_router.router)
app.include_router(network_monitor.router)
app.include_router(deliverables_router.router)


@app.get("/")
async def root():
    return {
        "status": "online",
        "mode": "SOVEREIGN_ON_PREM",
        "message": (
            "MRPL Agentic AI Workbench is running. "
            "No external network calls are made by this service."
        ),
    }


@app.on_event("startup")
async def startup_banner():
    logger.info("=" * 70)
    logger.info("MRPL SOVEREIGN AGENTIC AI WORKBENCH - STARTUP")
    logger.info(
        f"Local LLM endpoint: {settings.local_llm_base_url}"
    )
    logger.info(
        "All inference, embeddings, OCR, and vision run on-premise."
    )
    logger.info("=" * 70)