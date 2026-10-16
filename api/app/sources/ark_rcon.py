"""
FUENTE "ark_rcon"
=================
Pregunta directamente al juego por RCON cuántos jugadores hay conectados
(comando ListPlayers). Es lo que Pterodactyl no sabe.

Solo se CUENTAN los jugadores: los nombres e IDs que devuelve el juego no salen
nunca de este fichero.

Configuración en servers.yaml (los valores reales van en .env, nunca en el yaml):
    - type: ark_rcon
      env_prefix: RCON_GENESIS_1

Con ese prefijo se leen del .env:
    RCON_GENESIS_1_PORT       puerto RCON del servidor (obligatorio)
    RCON_GENESIS_1_HOST       si falta, se usa RCON_HOST (común a todos)
    RCON_GENESIS_1_PASSWORD   si falta, se usa RCON_PASSWORD (común a todos)
La contraseña es la ServerAdminPassword del servidor (con RCONEnabled=True).

Seguridad:
  - RCON viaja sin cifrar. Esta fuente SOLO se conecta a direcciones privadas
    (192.168.x.x, 10.x.x.x, 172.16-31.x.x o el propio equipo). Si el host es
    público, se niega a conectar. Si algún día la API está fuera de la red
    local, hay que llegar por WireGuard (que también usa direcciones privadas).
  - El puerto RCON nunca debe abrirse a Internet en el router.

Si el juego no responde (apagado, contraseña mal, tiempo agotado), la fuente
falla de forma controlada: el estado sigue viniendo de Pterodactyl y los
jugadores se muestran como "–".

Protocolo: Source RCON (el mismo que usan ARK y muchos otros juegos).
Cada paquete:  tamaño (int32) | id (int32) | tipo (int32) | texto | \\0\\0
"""
import asyncio
import ipaddress
import re
import socket
import struct
from typing import Any

from app.config import read_env
from app.sources.base import SourceError, SourceReport

# Tipos de paquete del protocolo
AUTH = 3
AUTH_RESPONSE = 2
EXECCOMMAND = 2

MAX_PACKET = 4096 + 14  # límite del protocolo; evita leer respuestas absurdas

# Una línea por jugador: "0. NombreJugador, 0002a1b2c3..."
PLAYER_LINE = re.compile(r"^\s*\d+\.\s")


def count_players(text: str) -> int:
    """Cuenta los jugadores de la respuesta de ListPlayers (sin guardar nombres)."""
    if "no players connected" in text.lower():
        return 0
    return sum(1 for line in text.splitlines() if PLAYER_LINE.match(line))


def encode_packet(request_id: int, packet_type: int, body: str) -> bytes:
    payload = struct.pack("<ii", request_id, packet_type) + body.encode("utf-8") + b"\x00\x00"
    return struct.pack("<i", len(payload)) + payload


async def read_packet(reader: asyncio.StreamReader) -> tuple[int, int, str]:
    (size,) = struct.unpack("<i", await reader.readexactly(4))
    if size < 10 or size > MAX_PACKET:
        raise SourceError("ark_rcon: respuesta con formato inesperado")
    data = await reader.readexactly(size)
    request_id, packet_type = struct.unpack("<ii", data[:8])
    return request_id, packet_type, data[8:-2].decode("utf-8", errors="replace")


async def resolve_private(host: str, port: int) -> str:
    """Devuelve la IP del host solo si es privada; si no, se niega."""
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceError(f"ark_rcon: no se encuentra el host '{host}'") from exc
    ips = {info[4][0] for info in infos}
    for ip in ips:
        addr = ipaddress.ip_address(ip)
        if not (addr.is_private or addr.is_loopback):
            raise SourceError(
                f"ark_rcon: '{host}' no es una dirección de red local; por seguridad no se conecta"
            )
    return sorted(ips)[0]


class ArkRconSource:
    type = "ark_rcon"

    async def fetch(self, slug: str, options: dict[str, Any]) -> SourceReport:
        host, port, password = self._config(slug, options)
        ip = await resolve_private(host, port)

        try:
            reader, writer = await asyncio.open_connection(ip, port)
        except OSError as exc:
            raise SourceError(f"ark_rcon: no se puede conectar con el puerto {port}") from exc

        try:
            # 1. Autenticación
            writer.write(encode_packet(1, AUTH, password))
            await writer.drain()
            while True:
                request_id, packet_type, _ = await read_packet(reader)
                if packet_type == AUTH_RESPONSE:
                    break
            if request_id == -1:
                raise SourceError("ark_rcon: contraseña RCON incorrecta")

            # 2. ListPlayers
            writer.write(encode_packet(2, EXECCOMMAND, "ListPlayers"))
            await writer.drain()
            _, _, text = await read_packet(reader)
        except (asyncio.IncompleteReadError, ConnectionError) as exc:
            raise SourceError("ark_rcon: el servidor cortó la conexión") from exc
        finally:
            writer.close()

        return SourceReport(source=self.type, state="online", players_current=count_players(text))

    @staticmethod
    def _config(slug: str, options: dict[str, Any]) -> tuple[str, int, str]:
        prefix = options.get("env_prefix")
        if not prefix:
            raise SourceError(f"ark_rcon: falta 'env_prefix' para '{slug}' en servers.yaml")

        host = read_env(f"{prefix}_HOST") or read_env("RCON_HOST")
        port = read_env(f"{prefix}_PORT")
        password = read_env(f"{prefix}_PASSWORD") or read_env("RCON_PASSWORD")

        missing = [name for name, value in (
            ("RCON_HOST", host), (f"{prefix}_PORT", port), ("RCON_PASSWORD", password),
        ) if not value]
        if missing:
            raise SourceError(f"ark_rcon: faltan en .env: {', '.join(missing)}")
        try:
            return host, int(port), password
        except ValueError as exc:
            raise SourceError(f"ark_rcon: {prefix}_PORT no es un número") from exc

    async def close(self) -> None:
        pass
