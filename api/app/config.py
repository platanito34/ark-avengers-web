"""
CONFIGURACIÓN DEL BACKEND
=========================
- Valores generales y secretos: variables de entorno o fichero .env (ver .env.example).
- Qué servidores existen y de dónde se saca su estado: servers.yaml.
"""
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=API_DIR / ".env", extra="ignore")

    # Cada cuántos segundos se consulta el estado de los servidores
    poll_interval_seconds: int = 30
    # Tiempo máximo de espera por cada fuente
    source_timeout_seconds: float = 5.0
    # Orígenes web que pueden llamar a la API (separados por comas)
    cors_origins: str = "http://localhost:4321"

    servers_file: Path = API_DIR / "servers.yaml"
    mock_dir: Path = API_DIR / "mock"

    # Pterodactyl
    #   simulated -> lee respuestas de ejemplo de mock/pterodactyl/ (formato real de la API)
    #   live      -> llama al panel de verdad
    pterodactyl_mode: Literal["simulated", "live"] = "simulated"
    pterodactyl_url: str = ""
    pterodactyl_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


class SourceConfig(BaseModel):
    """Una fuente de estado para un servidor. Las opciones extra dependen del tipo."""
    model_config = {"extra": "allow"}
    type: str

    @property
    def options(self) -> dict[str, Any]:
        return self.model_extra or {}


class ServerConfig(BaseModel):
    maintenance: bool = False
    sources: list[SourceConfig] = Field(default_factory=list)


def load_servers(path: Path) -> dict[str, ServerConfig]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {slug: ServerConfig(**(cfg or {})) for slug, cfg in (data.get("servers") or {}).items()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
