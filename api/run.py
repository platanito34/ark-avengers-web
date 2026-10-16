"""
ARRANQUE DE PRODUCCIÓN DE LA API
================================
Lo usa el servidor de Pterodactyl (egg genérico de Python, PY_FILE=api/run.py).
En desarrollo sigue usándose:  uvicorn app.main:app --reload

- Escucha en 0.0.0.0 y en el puerto que asigna Pterodactyl (variable SERVER_PORT).
- Sin --reload y con UN solo proceso: la caché y la consulta cada 30 s
  tienen que existir una sola vez.
- Confía en las cabeceras X-Forwarded-* solo si vienen de una IP de red
  local (Caddy en la Raspberry).

Cuando arranca, uvicorn escribe "Application startup complete": Pterodactyl
usa ese texto para saber que el servidor ya está en marcha.
"""
import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent


def get_port() -> int:
    """Puerto de Pterodactyl (SERVER_PORT); si no hay, PORT; si no, 8000."""
    return int(os.environ.get("SERVER_PORT") or os.environ.get("PORT") or 8000)


def main() -> None:
    # Pterodactyl arranca desde la raíz del repositorio: el código está en api/
    sys.path.insert(0, str(API_DIR))
    os.chdir(API_DIR)

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=get_port(),
        workers=1,
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
        log_level="info",
    )


if __name__ == "__main__":
    main()
