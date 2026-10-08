"""
FUENTE "mock": datos de prueba
==============================
Lee mock/status.yaml y devuelve esos valores con una pequeña variación de
jugadores en cada consulta, para que la web parezca viva.
Hace el papel que en producción hará el juego (RCON): jugadores, máximo y versión.
"""
import random
from pathlib import Path
from typing import Any

import yaml

from app.sources.base import SourceError, SourceReport


class MockSource:
    type = "mock"

    def __init__(self, mock_dir: Path):
        self._file = mock_dir / "status.yaml"

    def _load(self) -> dict[str, Any]:
        # Se relee en cada consulta: puedes editar el fichero sin reiniciar el backend
        return (yaml.safe_load(self._file.read_text(encoding="utf-8")) or {}).get("servers", {})

    async def fetch(self, slug: str, options: dict[str, Any]) -> SourceReport:
        data = self._load().get(slug)
        if data is None:
            raise SourceError(f"mock: no hay datos de prueba para '{slug}' en {self._file.name}")

        if options.get("fail"):
            raise SourceError("mock: fallo simulado")

        online = bool(data.get("online", True))
        players_max = data.get("players_max")
        players = data.get("players", 0) if online else 0
        if online and players_max:
            players = max(0, min(players_max, players + random.randint(-2, 2)))

        return SourceReport(
            source=self.type,
            state="online" if online else "offline",
            players_current=players,
            players_max=players_max,
            version=data.get("version"),
        )

    async def close(self) -> None:
        pass
