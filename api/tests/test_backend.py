"""
Tests del backend. Ejecutar desde la carpeta api/:   pytest
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.aggregator import merge_reports
from app.config import get_settings, load_servers
from app.schemas import StatusResponse
from app.sources.base import SourceReport
from app.sources.pterodactyl import parse_resources

API_DIR = Path(__file__).resolve().parent.parent
ROOT = API_DIR.parent
NOW = datetime.now(timezone.utc)


# ---------- Combinación de fuentes ----------
def test_pterodactyl_manda_en_el_estado_y_el_juego_en_los_jugadores():
    reports = [
        SourceReport(source="pterodactyl", state="online"),
        SourceReport(source="rcon", state="online", players_current=12, players_max=70, version="v1"),
    ]
    s = merge_reports("x", reports, maintenance=False, checked_at=NOW)
    assert s.state == "online" and s.players.current == 12 and s.version == "v1"


def test_si_pterodactyl_dice_offline_no_se_muestran_jugadores():
    reports = [
        SourceReport(source="pterodactyl", state="offline"),
        SourceReport(source="rcon", players_current=5, players_max=70),
    ]
    s = merge_reports("x", reports, maintenance=False, checked_at=NOW)
    assert s.state == "offline" and s.players.current is None


def test_sin_fuentes_que_respondan_es_unknown_no_offline():
    s = merge_reports("x", [], maintenance=False, checked_at=NOW)
    assert s.state == "unknown" and s.checked_at is None


def test_mantenimiento_tiene_prioridad():
    s = merge_reports("x", [SourceReport(source="p", state="online")], maintenance=True, checked_at=NOW)
    assert s.state == "maintenance"


# ---------- Lectura del formato de Pterodactyl ----------
@pytest.mark.parametrize("raw,expected", [
    ("running", "online"), ("starting", "starting"), ("stopping", "stopping"),
    ("offline", "offline"), ("algo-raro", "unknown"),
])
def test_estados_pterodactyl(raw, expected):
    payload = {"object": "stats", "attributes": {"current_state": raw, "is_suspended": False, "resources": {}}}
    assert parse_resources(payload).state == expected


def test_servidor_suspendido_es_offline():
    payload = {"attributes": {"current_state": "running", "is_suspended": True}}
    assert parse_resources(payload).state == "offline"


def test_respuestas_simuladas_tienen_formato_valido():
    for file in (API_DIR / "mock" / "pterodactyl").glob("*.json"):
        parse_resources(json.loads(file.read_text()))


# ---------- Contrato con la web ----------
def test_fixtures_de_la_web_cumplen_el_contrato():
    files = list((ROOT / "web" / "fixtures" / "status").glob("*.json"))
    assert files, "no se han encontrado fixtures"
    for file in files:
        StatusResponse.model_validate_json(file.read_text())


def test_servidores_backend_y_web_coinciden():
    # Compara con los servidores REALES (api/servers.yaml), no con los de prueba
    web = {p.stem for p in (ROOT / "web" / "src" / "content" / "servidores").glob("*.md")}
    api = set(load_servers(API_DIR / "servers.yaml"))
    assert web == api, f"Solo en la web: {web - api} | Solo en el backend: {api - web}"


# ---------- API ----------
def test_los_tests_no_usan_la_configuracion_real():
    # Ver conftest.py: nada de api/.env ni del panel
    settings = get_settings()
    assert settings.pterodactyl_mode == "simulated"
    assert settings.pterodactyl_api_key == ""
    assert settings.servers_file.name == "servers_prueba.yaml"


def test_api_responde():
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/api/status")
        assert r.status_code == 200
        data = StatusResponse.model_validate(r.json())
        by_slug = {s.slug: s for s in data.servers}
        states = {slug: s.state for slug, s in by_slug.items()}
        assert states == {
            "prueba-online": "online",
            "prueba-arrancando": "starting",
            "prueba-apagado": "offline",
            "prueba-mantenimiento": "maintenance",
            "prueba-solo-juego": "offline",
            "prueba-sin-datos": "unknown",
        }
        # Jugadores: de la fuente mock (con su pequeña variación aleatoria)
        assert by_slug["prueba-online"].players.max == 70
        assert 36 <= by_slug["prueba-online"].players.current <= 40

        assert client.get("/api/status/prueba-online").status_code == 200
        assert client.get("/api/status/no-existe").status_code == 404

        # Nada interno debe salir en la respuesta pública
        body = r.text
        for leak in ("1a7ce997", "memory_bytes", "cpu_absolute"):
            assert leak not in body
