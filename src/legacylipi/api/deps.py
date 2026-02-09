"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from legacylipi.api.session_manager import SessionManager

# The actual instance is set by main.py at startup
_session_manager: SessionManager | None = None


def set_session_manager(sm: SessionManager):
    global _session_manager
    _session_manager = sm


async def get_session_manager() -> SessionManager:
    if _session_manager is None:
        raise RuntimeError("SessionManager not initialized")
    return _session_manager


SessionManagerDep = Annotated[SessionManager, Depends(get_session_manager)]
