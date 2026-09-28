from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.config import settings
from app.core.security import get_current_user
from app.rag.knowledge_base import (
    ingest_document,
    kb_stats,
    query_knowledge_base,
)
from app.vision.ocr_vision import tesseract_extract_from_scanned_pdf

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    doc_type: str = Form("SOP"),
    is_scanned: bool = Form(False),
):
    original_filename = file.filename or "uploaded_document"
    extension = Path(original_filename).suffix.lower()
    save_path = Path(settings.upload_dir) / f"{uuid.uuid4().hex}{extension}"

    try:
        save_path.write_bytes(await file.read())
        ocr_text = None

        if is_scanned and extension == ".pdf":
            ocr_text = tesseract_extract_from_scanned_pdf(str(save_path), dpi=300)

        result = ingest_document(
            str(save_path),
            doc_type=doc_type,
            ocr_text=ocr_text,
            original_filename=original_filename,
        )
        return result
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {error}",
        ) from error


@router.get("/search")
async def search(q: str, top_k: int = 5):
    return query_knowledge_base(q, top_k=top_k)


@router.get("/stats")
async def stats():
    return kb_stats()
