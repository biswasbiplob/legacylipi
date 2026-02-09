"""Processing endpoints — start scan-copy, convert, or translate pipelines."""

import asyncio
import logging
import uuid

from fastapi import APIRouter, HTTPException

from legacylipi.api.deps import SessionManagerDep
from legacylipi.api.pipeline import run_convert, run_scan_copy, run_translate
from legacylipi.api.schemas import (
    ConvertRequest,
    JobResponse,
    ProgressEvent,
    ScanCopyRequest,
    TranslateRequest,
)
from legacylipi.api.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["processing"])


async def _run_pipeline(session_manager: SessionManager, session_id: str, coro):
    """Wrapper that runs a pipeline coroutine and stores the result."""
    session = await session_manager.get_session(session_id)
    if not session or not session.progress_queue:
        return

    try:
        result_bytes, result_filename = await coro
        await session_manager.set_result(session_id, result_bytes, result_filename)

        await session.progress_queue.put(
            ProgressEvent(
                status="complete",
                percent=100,
                step="complete",
                message="Done!",
                filename=result_filename,
                file_size=len(result_bytes),
            )
        )
    except Exception as e:
        logger.exception(f"Pipeline error for session {session_id}")
        session.is_processing = False
        if session.progress_queue:
            await session.progress_queue.put(
                ProgressEvent(
                    status="error",
                    message=str(e),
                )
            )


@router.post("/{session_id}/scan-copy", response_model=JobResponse)
async def start_scan_copy(
    session_id: str, request: ScanCopyRequest, session_manager: SessionManagerDep
):
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_processing:
        raise HTTPException(status_code=409, detail="Session is already processing")

    session.is_processing = True
    session.progress_queue = asyncio.Queue()
    job_id = str(uuid.uuid4())

    async def progress_cb(percent: int, step: str, message: str):
        if session.progress_queue:
            await session.progress_queue.put(
                ProgressEvent(status="processing", percent=percent, step=step, message=message)
            )

    coro = run_scan_copy(session.file_bytes, session.filename, request, progress_cb)
    asyncio.create_task(_run_pipeline(session_manager, session_id, coro))

    return JobResponse(job_id=job_id)


@router.post("/{session_id}/convert", response_model=JobResponse)
async def start_convert(
    session_id: str, request: ConvertRequest, session_manager: SessionManagerDep
):
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_processing:
        raise HTTPException(status_code=409, detail="Session is already processing")

    session.is_processing = True
    session.progress_queue = asyncio.Queue()
    job_id = str(uuid.uuid4())

    async def progress_cb(percent: int, step: str, message: str):
        if session.progress_queue:
            await session.progress_queue.put(
                ProgressEvent(status="processing", percent=percent, step=step, message=message)
            )

    coro = run_convert(session.file_bytes, session.filename, request, progress_cb)
    asyncio.create_task(_run_pipeline(session_manager, session_id, coro))

    return JobResponse(job_id=job_id)


@router.post("/{session_id}/translate", response_model=JobResponse)
async def start_translate(
    session_id: str, request: TranslateRequest, session_manager: SessionManagerDep
):
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.is_processing:
        raise HTTPException(status_code=409, detail="Session is already processing")

    session.is_processing = True
    session.progress_queue = asyncio.Queue()
    job_id = str(uuid.uuid4())

    async def progress_cb(percent: int, step: str, message: str):
        if session.progress_queue:
            await session.progress_queue.put(
                ProgressEvent(status="processing", percent=percent, step=step, message=message)
            )

    coro = run_translate(session.file_bytes, session.filename, request, progress_cb)
    asyncio.create_task(_run_pipeline(session_manager, session_id, coro))

    return JobResponse(job_id=job_id)
