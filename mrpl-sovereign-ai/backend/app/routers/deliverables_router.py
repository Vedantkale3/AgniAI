from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.core.security import get_current_user


router = APIRouter(
    prefix="/api/deliverables",
    tags=["deliverables"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/list")
async def list_deliverables():
    directory = Path(settings.deliverable_dir).resolve()

    if not directory.exists():
        return []

    files = [
        file_path
        for file_path in directory.iterdir()
        if file_path.is_file()
    ]

    files.sort(key=lambda file_path: file_path.stat().st_mtime, reverse=True)

    return [
        {
            "name": file_path.name,
            "size_kb": round(file_path.stat().st_size / 1024, 1),
        }
        for file_path in files
    ]


@router.get("/download/{filename}")
async def download(filename: str):
    directory = Path(settings.deliverable_dir).resolve()
    requested_path = (directory / filename).resolve()

    if requested_path.parent != directory:
        raise HTTPException(status_code=400, detail="Invalid filename")

    if not requested_path.is_file():
        raise HTTPException(status_code=404, detail="Deliverable not found")

    return FileResponse(
        path=str(requested_path),
        filename=requested_path.name,
        content_disposition_type="attachment",
    )
