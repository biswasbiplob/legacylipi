"""In-memory session store with TTL-based cleanup."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 30 * 60  # 30 minutes
CLEANUP_INTERVAL_SECONDS = 60  # Check every minute


@dataclass
class SessionData:
    """Data stored per upload session."""

    session_id: str
    filename: str
    file_bytes: bytes
    file_size: int
    created_at: float = field(default_factory=time.time)

    # Processing state
    is_processing: bool = False
    progress_queue: asyncio.Queue | None = None

    # Result
    result_bytes: bytes | None = None
    result_filename: str | None = None


class SessionManager:
    """Manages upload sessions with automatic TTL expiry."""

    def __init__(self, ttl: int = SESSION_TTL_SECONDS):
        self._sessions: dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
        self._ttl = ttl
        self._cleanup_task: asyncio.Task | None = None

    async def start_cleanup(self):
        """Start the background cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self):
        """Stop the background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """Periodically remove expired sessions."""
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            await self._expire_sessions()

    async def _expire_sessions(self):
        """Remove sessions older than TTL."""
        now = time.time()
        async with self._lock:
            expired = [
                sid
                for sid, session in self._sessions.items()
                if (now - session.created_at) > self._ttl and not session.is_processing
            ]
            for sid in expired:
                del self._sessions[sid]
                logger.info(f"Expired session {sid}")

    async def create_session(self, filename: str, file_bytes: bytes) -> SessionData:
        """Create a new session for an uploaded file."""
        session_id = str(uuid.uuid4())
        session = SessionData(
            session_id=session_id,
            filename=filename,
            file_bytes=file_bytes,
            file_size=len(file_bytes),
            progress_queue=asyncio.Queue(),
        )
        async with self._lock:
            self._sessions[session_id] = session
        logger.info(f"Created session {session_id} for {filename} ({len(file_bytes)} bytes)")
        return session

    async def get_session(self, session_id: str) -> SessionData | None:
        """Get a session by ID."""
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session. Returns True if found and deleted."""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            return False

    async def set_result(self, session_id: str, result_bytes: bytes, result_filename: str) -> bool:
        """Store processing results for a session."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.result_bytes = result_bytes
                session.result_filename = result_filename
                session.is_processing = False
                return True
            return False
