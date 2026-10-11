"""
Configuración común de los tests (pytest la carga antes que los tests).

Los tests NO dependen de api/.env ni del panel de Pterodactyl:
- modo simulated (lee mock/pterodactyl/*.json en vez de llamar al panel),
- servidores de prueba propios (tests/servers_prueba.yaml),
- sin URL ni clave del panel.
"""
import os
from pathlib import Path

from app.config import Settings, get_settings

TESTS_DIR = Path(__file__).resolve().parent

# No leer api/.env (ahí está la configuración real)
Settings.model_config["env_file"] = None

# Las variables de entorno mandan sobre los valores por defecto: las fijamos todas
os.environ.update({
    "PTERODACTYL_MODE": "simulated",
    "PTERODACTYL_URL": "",
    "PTERODACTYL_API_KEY": "",
    "SERVERS_FILE": str(TESTS_DIR / "servers_prueba.yaml"),
    "MOCK_DIR": str(TESTS_DIR.parent / "mock"),
})
get_settings.cache_clear()
