"""
Tests del arranque de producción (api/run.py): el puerto sale de Pterodactyl.
"""
import run


def test_puerto_de_pterodactyl(monkeypatch):
    monkeypatch.setenv("SERVER_PORT", "8123")
    monkeypatch.setenv("PORT", "9999")
    assert run.get_port() == 8123


def test_puerto_alternativo(monkeypatch):
    monkeypatch.delenv("SERVER_PORT", raising=False)
    monkeypatch.setenv("PORT", "9999")
    assert run.get_port() == 9999


def test_puerto_por_defecto(monkeypatch):
    monkeypatch.delenv("SERVER_PORT", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    assert run.get_port() == 8000
