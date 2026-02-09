"""SSE progress streaming endpoint."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

from legacylipi.api.deps import SessionManagerDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["progress"])


@router.get("/{session_id}/progress", response_model=None)
async def stream_progress(session_id: str, session_manager: SessionManagerDep):
    """Stream processing progress as Server-Sent Events."""
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        queue = session.progress_queue
        if not queue:
            yield 'data: {"status": "error", "message": "No active processing"}\n\n'
            return

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {event.model_dump_json()}\n\n"
                if event.status in ("complete", "error"):
                    break
            except TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
