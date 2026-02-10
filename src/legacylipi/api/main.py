"""FastAPI application for LegacyLipi.

Serves the REST API and (in production) the built React frontend as static files.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from legacylipi import __version__
from legacylipi.api.deps import set_session_manager
from legacylipi.api.routes import config, download, processing, progress, sessions
from legacylipi.api.schemas import HealthResponse
from legacylipi.api.session_manager import SessionManager

logger = logging.getLogger(__name__)

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


app = FastAPI(
    title="LegacyLipi API",
    description="REST API for translating PDFs with legacy Indian font encodings",
    version=__version__,
    lifespan=lifespan,
)

# CORS for development (Vite dev server on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(config.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(processing.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(download.router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version=__version__)


# Serve frontend static files in production.
# Check two locations: bundled inside the package (installed), or in the project tree (dev).
_pkg_static = Path(__file__).parent / "static"
_project_static = Path(__file__).parent.parent.parent.parent / "frontend" / "dist"
_frontend_dist = _pkg_static if _pkg_static.exists() else _project_static
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


def serve(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for the legacylipi-web command."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    serve()
