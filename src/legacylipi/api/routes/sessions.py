"""Session management endpoints — upload and delete."""

from fastapi import APIRouter, HTTPException, UploadFile

from legacylipi.api.deps import SessionManagerDep
from legacylipi.api.schemas import UploadResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile, session_manager: SessionManagerDep):
    """Upload a PDF file and create a processing session."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(contents) > 50_000_000:  # 50 MB
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    session = await session_manager.create_session(file.filename, contents)
    return UploadResponse(
        session_id=session.session_id,
        filename=session.filename,
        file_size=session.file_size,
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str, session_manager: SessionManagerDep):
    """Delete a session and its data."""
    deleted = await session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}
