"""
COMBINACIÓN DE FUENTES
======================
Un servidor puede tener varias fuentes (p. ej. Pterodactyl + RCON). Aquí se
decide qué dato gana. Reglas:

  1. Si el servidor está marcado `maintenance: true` en servers.yaml -> "maintenance".
  2. Estado: gana la PRIMERA fuente de la lista (en el orden de servers.yaml)
     que haya devuelto un estado. Por eso Pterodactyl va primero: sabe si el
     proceso está encendido de verdad.
  3. Jugadores y versión: el primer valor no vacío de cualquier fuente.
  4. Si ninguna fuente ha respondido -> "unknown". Nunca decimos "offline" sin saberlo.
  5. Solo se muestran jugadores cuando el estado es "online".
"""
from datetime import datetime

from app.schemas import Players, ServerStatus
from app.sources.base import SourceReport


def _first(values):
    return next((v for v in values if v is not None), None)


def merge_reports(slug: str, reports: list[SourceReport], maintenance: bool, checked_at: datetime) -> ServerStatus:
    if maintenance:
        return ServerStatus(slug=slug, state="maintenance", checked_at=checked_at)

    state = _first(r.state for r in reports) or "unknown"

    players = Players()
    if state == "online":
        players = Players(
            current=_first(r.players_current for r in reports),
            max=_first(r.players_max for r in reports),
        )

    return ServerStatus(
        slug=slug,
        state=state,
        players=players,
        version=_first(r.version for r in reports) if state == "online" else None,
        checked_at=checked_at if reports else None,
    )
