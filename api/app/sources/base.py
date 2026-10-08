"""
INTERFAZ COMÚN DE LAS FUENTES DE ESTADO
=======================================
Cada fuente (Pterodactyl, el propio juego vía RCON, datos de prueba...) sabe
consultar una parte del estado de un servidor y devuelve un SourceReport.
Cada fuente rellena solo lo que sabe; el resto lo deja en None.

  Pterodactyl -> sabe si el proceso está encendido (state). NO sabe cuántos jugadores hay.
  ARK (RCON)  -> sabe jugadores y versión. Si responde, el juego está online.
  Mock        -> datos de prueba para desarrollar sin infraestructura.

Para añadir una fuente nueva:
  1. Crea un fichero en esta carpeta con una clase que tenga `type` y `fetch()`.
  2. Regístrala en app/sources/__init__.py.
  3. Úsala en servers.yaml.
"""
from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas import PublicState


@dataclass
class SourceReport:
    source: str
    state: PublicState | None = None
    players_current: int | None = None
    players_max: int | None = None
    version: str | None = None


class SourceError(Exception):
    """La fuente no ha podido dar datos (caída, timeout, mal configurada...)."""


class StatusSource(Protocol):
    type: str

    async def fetch(self, slug: str, options: dict[str, Any]) -> SourceReport: ...

    async def close(self) -> None: ...
