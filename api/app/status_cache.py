"""
CONSULTA PERIÓDICA Y MEMORIA CACHÉ
==================================
El backend consulta las fuentes cada POLL_INTERVAL_SECONDS en segundo plano y
guarda el resultado. Las visitas a la web solo leen esta copia: aunque entren
cien personas, los servidores de juego reciben una consulta cada X segundos.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.aggregator import merge_reports
from app.config import ServerConfig
from app.schemas import ServerStatus
from app.sources import SourceError, SourceReport, StatusSource

log = logging.getLogger("status")


class StatusCache:
    def __init__(self, servers: dict[str, ServerConfig], sources: dict[str, StatusSource], timeout: float):
        self.servers = servers
        self.sources = sources
        self.timeout = timeout
        self.last_refresh: datetime | None = None
        self._data: dict[str, ServerStatus] = {
            slug: ServerStatus(slug=slug, state="unknown") for slug in servers
        }
        self._task: asyncio.Task | None = None

    # ---------- lectura (lo que usa la API) ----------
    def all(self) -> list[ServerStatus]:
        return list(self._data.values())

    def get(self, slug: str) -> ServerStatus | None:
        return self._data.get(slug)

    # ---------- consulta ----------
    async def _query(self, slug: str, source_cfg) -> SourceReport | None:
        source = self.sources.get(source_cfg.type)
        if source is None:
            log.warning("'%s': tipo de fuente desconocido '%s'", slug, source_cfg.type)
            return None
        try:
            return await asyncio.wait_for(source.fetch(slug, source_cfg.options), timeout=self.timeout)
        except asyncio.TimeoutError:
            log.warning("'%s': la fuente %s no respondió a tiempo", slug, source_cfg.type)
        except SourceError as exc:
            log.warning("'%s': %s", slug, exc)
        except Exception:  # un fallo en una fuente nunca debe tumbar el backend
            log.exception("'%s': error inesperado en la fuente %s", slug, source_cfg.type)
        return None

    async def _refresh_one(self, slug: str, cfg: ServerConfig) -> ServerStatus:
        results = await asyncio.gather(*(self._query(slug, s) for s in cfg.sources))
        reports = [r for r in results if r is not None]
        return merge_reports(slug, reports, cfg.maintenance, datetime.now(timezone.utc))

    async def refresh(self) -> None:
        slugs = list(self.servers)
        results = await asyncio.gather(*(self._refresh_one(s, self.servers[s]) for s in slugs))
        self._data = dict(zip(slugs, results))
        self.last_refresh = datetime.now(timezone.utc)

    # ---------- bucle en segundo plano ----------
    def start(self, interval: int) -> None:
        async def loop():
            while True:
                try:
                    await self.refresh()
                except Exception:
                    log.exception("Error refrescando el estado")
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        for source in self.sources.values():
            await source.close()
