"""
CONTRATO PÚBLICO DE LA API
==========================
Estos modelos definen exactamente lo que la web recibe del backend.
Si cambias algo aquí, cambia también:
  - web/src/lib/status-types.ts   (los mismos tipos en TypeScript)
  - web/fixtures/status/*.json     (los datos de ejemplo de la web)
Los tests (tests/test_contract.py) avisan si los fixtures dejan de cumplir el contrato.

Nunca añadas aquí datos internos: IPs, IDs de Pterodactyl, CPU/RAM, contraseñas
ni nombres de jugadores.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Estados públicos de un servidor.
#   online       -> el servidor está en marcha
#   starting     -> arrancando
#   stopping     -> apagándose
#   offline      -> apagado
#   maintenance  -> marcado a mano como "en mantenimiento"
#   unknown      -> no hemos podido saberlo (no es lo mismo que offline)
PublicState = Literal["online", "starting", "stopping", "offline", "maintenance", "unknown"]


class Players(BaseModel):
    current: int | None = Field(default=None, ge=0)
    max: int | None = Field(default=None, ge=0)


class ServerStatus(BaseModel):
    slug: str
    state: PublicState
    players: Players = Field(default_factory=Players)
    version: str | None = None
    checked_at: datetime | None = None


class StatusResponse(BaseModel):
    servers: list[ServerStatus]
    generated_at: datetime
