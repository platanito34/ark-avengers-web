"""
API PÚBLICA DE LOS SERVIDORES DE ARK
====================================
Arrancar en desarrollo (desde la carpeta api/):
    uvicorn app.main:app --reload

Documentación interactiva: http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, load_servers
from app.schemas import ServerStatus, StatusResponse
from app.sources import build_sources
from app.status_cache import StatusCache

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

CACHE_HEADER = "public, max-age=15"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    cache = StatusCache(
        servers=load_servers(settings.servers_file),
        sources=build_sources(settings),
        timeout=settings.source_timeout_seconds,
    )
    await cache.refresh()  # primer estado antes de aceptar visitas
    cache.start(settings.poll_interval_seconds)
    app.state.cache = cache
    yield
    await cache.stop()


app = FastAPI(
    title="Servidores de ARK — API pública",
    version="0.1.0",
    description="Estado público de los servidores. Solo lectura.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/status", response_model=StatusResponse, tags=["estado"])
def get_all_status(response: Response):
    """Estado de todos los servidores configurados."""
    response.headers["Cache-Control"] = CACHE_HEADER
    return StatusResponse(servers=app.state.cache.all(), generated_at=datetime.now(timezone.utc))


@app.get("/api/status/{slug}", response_model=ServerStatus, tags=["estado"])
def get_server_status(slug: str, response: Response):
    """Estado de un servidor concreto."""
    status = app.state.cache.get(slug)
    if status is None:
        raise HTTPException(status_code=404, detail="Servidor no encontrado")
    response.headers["Cache-Control"] = CACHE_HEADER
    return status


@app.get("/api/health", tags=["sistema"])
def health():
    """Para comprobar que el backend está vivo."""
    cache = app.state.cache
    return {
        "ok": True,
        "servers": len(cache.servers),
        "last_refresh": cache.last_refresh,
        "pterodactyl_mode": get_settings().pterodactyl_mode,
    }
