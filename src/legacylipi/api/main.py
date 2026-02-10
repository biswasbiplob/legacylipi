"""FastAPI application for LegacyLipi.

Serves the REST API and (in production) the built React frontend as static files.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
except ImportError as _e:
    _missing = _e
    # Allow the module to be imported for introspection, but block serve()/create_app().
    uvicorn = None  # type: ignore[assignment]
    FastAPI = None  # type: ignore[assignment,misc]
else:
    _missing = None  # type: ignore[assignment]

from legacylipi import __version__

logger = logging.getLogger(__name__)


def _check_deps() -> None:
    """Raise a clear error when API dependencies are not installed."""
    if _missing is not None:
        raise ImportError(
            f"API dependencies not installed: {_missing}\n"
            "Install with: pip install 'legacylipi[api]' or uv pip install 'legacylipi[api]'"
        ) from _missing


def create_app() -> "FastAPI":
    """Build and return the FastAPI application instance."""
    _check_deps()

    from legacylipi.api.deps import set_session_manager
    from legacylipi.api.routes import config, download, processing, progress, sessions
    from legacylipi.api.schemas import HealthResponse
    from legacylipi.api.session_manager import SessionManager

    _session_manager = SessionManager()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan — start/stop background tasks."""
        set_session_manager(_session_manager)
        logger.info("Starting LegacyLipi API...")
        await _session_manager.start_cleanup()
        yield
        logger.info("Shutting down LegacyLipi API...")
        await _session_manager.stop_cleanup()

    application = FastAPI(
        title="LegacyLipi API",
        description="REST API for translating PDFs with legacy Indian font encodings",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS for development (Vite dev server on port 5173)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    application.include_router(config.router, prefix="/api/v1")
    application.include_router(sessions.router, prefix="/api/v1")
    application.include_router(processing.router, prefix="/api/v1")
    application.include_router(progress.router, prefix="/api/v1")
    application.include_router(download.router, prefix="/api/v1")

    @application.get("/api/v1/health", response_model=HealthResponse)
    async def health():
        return HealthResponse(status="ok", version=__version__)

    # Serve frontend static files in production.
    # Check two locations: bundled inside the package (installed), or in the project tree (dev).
    _pkg_static = Path(__file__).parent / "static"
    _project_static = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
    _frontend_dist = _pkg_static if _pkg_static.exists() else _project_static
    if _frontend_dist.exists():
        application.mount(
            "/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend"
        )

    return application


# Module-level app for backward compatibility (tests, ASGI servers).
# Created lazily only when API deps are available.
if FastAPI is not None:
    app = create_app()
else:
    app = None  # type: ignore[assignment]


def serve(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for the legacylipi-web command."""
    _check_deps()
    global app  # noqa: PLW0603
    if app is None:
        app = create_app()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve()
