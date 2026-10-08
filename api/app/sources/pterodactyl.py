"""
FUENTE "pterodactyl"
====================
Consulta el estado del proceso de un servidor en Pterodactyl mediante su
API de cliente:  GET {PANEL}/api/client/servers/{server_id}/resources

Solo usamos `current_state`. La CPU, RAM, disco, etc. también vienen en la
respuesta, pero NO se pasan a la web pública.

Modos (variable PTERODACTYL_MODE):
  simulated -> lee mock/pterodactyl/{server_id}.json, que tiene el mismo formato
               que la respuesta real. Así el código de lectura ya está probado.
  live      -> llama al panel real con PTERODACTYL_URL y PTERODACTYL_API_KEY.

Clave de API: crea en Pterodactyl un usuario dedicado para el backend, añádelo
como subusuario de cada servidor con los permisos mínimos y genera una clave de
API de cliente con ese usuario. Nunca uses la clave de un administrador.

En servers.yaml:
    - type: pterodactyl
      server_id: "1a7ce997"     # identificador corto que ves en la URL del panel
"""
import json
from pathlib import Path
from typing import Any

import httpx

from app.schemas import PublicState
from app.sources.base import SourceError, SourceReport

# Estados de Pterodactyl -> estados públicos
STATE_MAP: dict[str, PublicState] = {
    "running": "online",
    "starting": "starting",
    "stopping": "stopping",
    "offline": "offline",
}


def parse_resources(payload: dict[str, Any]) -> SourceReport:
    """Convierte la respuesta de /resources en un SourceReport."""
    try:
        attrs = payload["attributes"]
        raw_state = attrs["current_state"]
    except (KeyError, TypeError) as exc:
        raise SourceError("pterodactyl: respuesta con formato inesperado") from exc

    if attrs.get("is_suspended"):
        state: PublicState = "offline"
    else:
        state = STATE_MAP.get(raw_state, "unknown")

    return SourceReport(source="pterodactyl", state=state)


class PterodactylSource:
    type = "pterodactyl"

    def __init__(self, mode: str, mock_dir: Path, url: str = "", api_key: str = "", timeout: float = 5.0):
        self.mode = mode
        self._mock_dir = mock_dir / "pterodactyl"
        self._client: httpx.AsyncClient | None = None

        if mode == "live":
            if not url or not api_key:
                raise ValueError("PTERODACTYL_MODE=live necesita PTERODACTYL_URL y PTERODACTYL_API_KEY")
            self._client = httpx.AsyncClient(
                base_url=url.rstrip("/"),
                timeout=timeout,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            )

    async def fetch(self, slug: str, options: dict[str, Any]) -> SourceReport:
        server_id = options.get("server_id")
        if not server_id:
            raise SourceError(f"pterodactyl: falta 'server_id' para '{slug}' en servers.yaml")

        if self.mode == "simulated":
            file = self._mock_dir / f"{server_id}.json"
            if not file.exists():
                raise SourceError(f"pterodactyl (simulado): no existe {file.name}")
            payload = json.loads(file.read_text(encoding="utf-8"))
        else:
            try:
                resp = await self._client.get(f"/api/client/servers/{server_id}/resources")
                resp.raise_for_status()
                payload = resp.json()
            except httpx.HTTPError as exc:
                raise SourceError(f"pterodactyl: error consultando '{server_id}': {exc}") from exc

        return parse_resources(payload)

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
