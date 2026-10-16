"""
Tests de la fuente ark_rcon. No usan ningún servidor real: levantan un servidor
RCON falso en 127.0.0.1 que responde como lo haría ARK.
"""
import asyncio
import struct
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.aggregator import merge_reports
from app.config import load_servers
from app.sources.ark_rcon import ArkRconSource, count_players, encode_packet
from app.sources.base import SourceError, SourceReport

API_DIR = Path(__file__).resolve().parent.parent

PASSWORD = "clave-de-prueba"
DOS_JUGADORES = "0. Ana Superviviente, 0002a1b2c3d4e5f6\n1. Bob El Domador, 0002ffeeddccbbaa0\n"


# ---------- Servidor RCON falso ----------
async def _servidor_falso(respuesta: str, password: str = PASSWORD):
    async def atender(reader, writer):
        try:
            while True:
                size = struct.unpack("<i", await reader.readexactly(4))[0]
                data = await reader.readexactly(size)
                request_id, tipo = struct.unpack("<ii", data[:8])
                cuerpo = data[8:-2].decode()
                if tipo == 3:  # autenticación (ARK manda antes un paquete vacío)
                    writer.write(encode_packet(request_id, 0, ""))
                    writer.write(encode_packet(request_id if cuerpo == password else -1, 2, ""))
                elif cuerpo == "ListPlayers":
                    writer.write(encode_packet(request_id, 0, respuesta))
                await writer.drain()
        except asyncio.IncompleteReadError:
            pass
        finally:
            writer.close()

    server = await asyncio.start_server(atender, "127.0.0.1", 0)
    return server, server.sockets[0].getsockname()[1]


def _consultar(monkeypatch, respuesta=DOS_JUGADORES, password=PASSWORD, host="127.0.0.1"):
    async def run():
        server, port = await _servidor_falso(respuesta)
        monkeypatch.setenv("RCON_HOST", host)
        monkeypatch.setenv("RCON_PASSWORD", password)
        monkeypatch.setenv("RCON_PRUEBA_PORT", str(port))
        try:
            return await ArkRconSource().fetch("prueba", {"env_prefix": "RCON_PRUEBA"})
        finally:
            server.close()
            await server.wait_closed()

    return asyncio.run(run())


# ---------- Lectura de ListPlayers ----------
@pytest.mark.parametrize("texto,esperado", [
    ("No Players Connected", 0),
    ("No Players Connected\n", 0),
    ("", 0),
    (DOS_JUGADORES, 2),
    ("0. Solo Uno, 0002abc\n", 1),
])
def test_cuenta_jugadores(texto, esperado):
    assert count_players(texto) == esperado


# ---------- Conexión completa con el servidor falso ----------
def test_cuenta_jugadores_por_rcon(monkeypatch):
    report = _consultar(monkeypatch)
    assert report.state == "online" and report.players_current == 2


def test_nunca_salen_nombres_de_jugadores(monkeypatch):
    report = _consultar(monkeypatch)
    texto = repr(report)
    for dato in ("Ana", "Bob", "0002a1b2c3d4e5f6"):
        assert dato not in texto


def test_sin_jugadores(monkeypatch):
    assert _consultar(monkeypatch, respuesta="No Players Connected").players_current == 0


def test_contrasena_incorrecta(monkeypatch):
    with pytest.raises(SourceError, match="contraseña"):
        _consultar(monkeypatch, password="otra")


def test_el_error_no_muestra_la_contrasena(monkeypatch):
    with pytest.raises(SourceError) as exc:
        _consultar(monkeypatch, password="secreto-que-no-debe-salir")
    assert "secreto-que-no-debe-salir" not in str(exc.value)


def test_servidor_que_no_responde(monkeypatch):
    # Puerto cerrado: nadie escucha
    monkeypatch.setenv("RCON_HOST", "127.0.0.1")
    monkeypatch.setenv("RCON_PASSWORD", PASSWORD)
    monkeypatch.setenv("RCON_PRUEBA_PORT", "1")
    with pytest.raises(SourceError):
        asyncio.run(ArkRconSource().fetch("prueba", {"env_prefix": "RCON_PRUEBA"}))


# ---------- Seguridad y configuración ----------
@pytest.mark.parametrize("host", ["8.8.8.8", "1.1.1.1"])
def test_se_niega_a_conectar_con_direcciones_publicas(monkeypatch, host):
    with pytest.raises(SourceError, match="red local"):
        _consultar(monkeypatch, host=host)


def test_falta_configuracion(monkeypatch):
    for var in ("RCON_HOST", "RCON_PASSWORD", "RCON_PRUEBA_PORT"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SourceError, match="faltan en .env"):
        asyncio.run(ArkRconSource().fetch("prueba", {"env_prefix": "RCON_PRUEBA"}))


def test_servidores_reales_usan_pterodactyl_y_despues_rcon():
    for slug, cfg in load_servers(API_DIR / "servers.yaml").items():
        tipos = [s.type for s in cfg.sources]
        assert tipos == ["pterodactyl", "ark_rcon"], slug
        assert cfg.sources[1].options.get("env_prefix"), slug


# ---------- Si RCON falla, manda Pterodactyl ----------
def test_si_rcon_falla_se_mantiene_el_estado_de_pterodactyl():
    # RCON no aparece en la lista: es lo que pasa cuando falla
    s = merge_reports("x", [SourceReport(source="pterodactyl", state="online")],
                      maintenance=False, checked_at=datetime.now(timezone.utc))
    assert s.state == "online" and s.players.current is None
