"""AGNI AI local knowledge base with safe OCR ingestion and hybrid search."""

import hashlib
import os
import re
import uuid
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import docx2txt
from pypdf import PdfReader

from app.config import settings

MIN_RELEVANCE = 0.15
COLLECTION_NAME = "agni_knowledge_base"

client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2",
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function,
)


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _chunks(text: str, size: int = 500, overlap: int = 75) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    output = []
    for start in range(0, len(words), step):
        value = " ".join(words[start:start + size]).strip()
        if value:
            output.append(value)
        if start + size >= len(words):
            break
    return output


def extract_text(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    if suffix == ".docx":
        return docx2txt.process(str(path)).strip()
    return path.read_text(encoding="utf-8", errors="replace").strip()


def ingest_document(
    file_path: str,
    doc_type: str = "SOP",
    ocr_text: str | None = None,
    original_filename: str | None = None,
) -> dict:
    text = (ocr_text or extract_text(file_path)).strip()
    if not text:
        raise ValueError("No readable text was extracted from this document.")

    source = original_filename or Path(file_path).name
    source_key = hashlib.sha256(source.lower().encode()).hexdigest()[:24]

    old = collection.get(where={"source_key": source_key})
    if old.get("ids"):
        collection.delete(ids=old["ids"])

    values = _chunks(text)
    if not values:
        raise ValueError("Document could not be divided into searchable chunks.")

    ids = [str(uuid.uuid4()) for _ in values]
    metadata = [
        {
            "source": source,
            "source_key": source_key,
            "stored_name": Path(file_path).name,
            "doc_type": doc_type,
            "chunk_index": index,
        }
        for index in range(len(values))
    ]
    collection.add(documents=values, ids=ids, metadatas=metadata)

    return {
        "file": source,
        "chunks_ingested": len(values),
        "characters_extracted": len(text),
        "doc_type": doc_type,
    }


def _keyword_score(query: str, text: str) -> float:
    query_terms = set(_normalise(query).split())
    text_terms = set(_normalise(text).split())
    if not query_terms:
        return 0.0
    return len(query_terms & text_terms) / len(query_terms)


def query_knowledge_base(
    query: str,
    top_k: int = 5,
    doc_type_filter: str | None = None,
    min_relevance: float = MIN_RELEVANCE,
) -> list[dict]:
    query = query.strip()
    if not query or collection.count() == 0:
        return []

    where = {"doc_type": doc_type_filter} if doc_type_filter else None
    limit = min(max(top_k * 4, top_k), collection.count())
    result = collection.query(
        query_texts=[query],
        n_results=limit,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    documents = (result.get("documents") or [[]])[0]
    metadatas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    candidates = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        metadata = metadata or {}
        semantic = max(0.0, 1.0 - float(distance))
        keyword = _keyword_score(query, document)
        score = round((semantic * 0.75) + (keyword * 0.25), 3)
        candidates.append({
            "text": document,
            "source": metadata.get("source", "Local Knowledge Base"),
            "doc_type": metadata.get("doc_type", "UNKNOWN"),
            "chunk_index": metadata.get("chunk_index", 0),
            "relevance": score,
            "distance": round(float(distance), 3),
            "low_confidence": score < min_relevance,
        })

    candidates.sort(key=lambda item: item["relevance"], reverse=True)
    return [item for item in candidates if item["relevance"] >= min_relevance][:top_k]


def build_grounded_context(query: str, top_k: int = 5) -> str:
    hits = query_knowledge_base(query, top_k=top_k)
    if not hits:
        return (
            "NO_RELEVANT_INTERNAL_EVIDENCE_FOUND. Do not invent facts. Ask the "
            "user to ingest or attach the correct local source document."
        )
    return "\n\n---\n\n".join(
        f"[Source: {item['source']} | Type: {item['doc_type']} | "
        f"Relevance: {item['relevance']}]\n{item['text']}"
        for item in hits
    )


def kb_stats() -> dict:
    return {"total_chunks": collection.count()}
