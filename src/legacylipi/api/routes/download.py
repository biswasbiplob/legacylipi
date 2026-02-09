"""Download endpoint — retrieve processing results."""

from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from legacylipi.api.deps import SessionManagerDep

router = APIRouter(prefix="/sessions", tags=["download"])


@router.get("/{session_id}/download", response_model=None)
async def download_result(session_id: str, session_manager: SessionManagerDep):
    """Download the processing result file."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.result_bytes or not session.result_filename:
        raise HTTPException(status_code=404, detail="No result available yet")

    filename = session.result_filename
    if filename.endswith(".pdf"):
        content_type = "application/pdf"
    elif filename.endswith(".md"):
        content_type = "text/markdown; charset=utf-8"
    else:
        content_type = "text/plain; charset=utf-8"

    return Response(
        content=session.result_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
