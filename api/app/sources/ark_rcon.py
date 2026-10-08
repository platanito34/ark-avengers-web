"""
FUENTE "ark_rcon"  —  PREPARADA, SIN IMPLEMENTAR
===============================================
Consultará directamente el juego por RCON para obtener lo que Pterodactyl no
sabe: jugadores conectados y versión. Si el juego responde, también sabemos que
está online aunque el servidor no esté en Pterodactyl (por ejemplo, los que hoy
funcionan en Windows Server).

Configuración prevista en servers.yaml (los valores reales van en .env, nunca en el yaml):
    - type: ark_rcon
      host_env: ISLAND_RCON_HOST
      port_env: ISLAND_RCON_PORT
      password_env: ISLAND_RCON_PASSWORD

Seguridad: RCON viaja sin cifrar. El puerto RCON nunca debe abrirse a Internet;
el backend debe llegar a él por la red local o por el túnel WireGuard.

Mientras no esté implementada, cualquier servidor que la use simplemente no
obtendrá estos datos (el resto de fuentes siguen funcionando).
"""
from typing import Any

from app.sources.base import SourceError, SourceReport


class ArkRconSource:
    type = "ark_rcon"

    async def fetch(self, slug: str, options: dict[str, Any]) -> SourceReport:
        raise SourceError("ark_rcon: fuente todavía no implementada")

    async def close(self) -> None:
        pass
