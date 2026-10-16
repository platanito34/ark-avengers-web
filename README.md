# ARK Avengers — web de los servidores de ARK

> El nombre y el subtítulo se cambian solo en `web/src/config/site.ts`.
> En los ficheros Markdown se escribe `{nombre}` y la web lo sustituye.

```
web/   Web pública (Astro)          → lo que ven los jugadores
api/   Backend propio (FastAPI)     → estado de los servidores, único intermediario
```

```
Navegador → Web (estática) → API propia → Pterodactyl / juego (RCON) / datos de prueba
```

La web **nunca** habla con Pterodactyl ni con los servidores de juego. Solo con la API.

> ⚠️ Todos los servidores, textos, rates, mods y normas son **de ejemplo**.
> Revísalos antes de publicar (los ficheros llevan la marca "DATOS DE EJEMPLO" o "TEXTO PROVISIONAL").

---

## Arrancar en tu ordenador

Necesitas **Node.js 20 o superior** y **Python 3.11 o superior**.

### 1. La web (sin backend, con datos de ejemplo)

```bash
cd web
npm install          # solo la primera vez
npm run dev
```

Abre http://localhost:4321

Para ver otros escenarios añade a la URL `?escenario=problemas`, `?escenario=sin-jugadores`, `?escenario=vacio` o `?escenario=error`.

### 2. El backend

```bash
cd api
python -m venv .venv
.venv\Scripts\activate          # Windows   (en Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env          # Windows   (en Linux/Mac: cp .env.example .env)
uvicorn app.main:app --reload
```

- Estado: http://localhost:8000/api/status
- Documentación interactiva (puedes probar las llamadas): http://localhost:8000/docs

### 3. Conectar la web al backend

En `web/` copia `.env.example` como `.env` y cambia:

```
PUBLIC_STATUS_SOURCE=api
```

Reinicia `npm run dev`. Ahora el estado viene del backend.

### Tests del backend

```bash
cd api
pytest
```

Comprueban, entre otras cosas, que los datos de ejemplo de la web cumplen el formato de la API y que
la web y el backend tienen exactamente los mismos servidores.

---

## Dónde se cambia cada cosa

| Quiero cambiar…                         | Fichero                                              |
|-----------------------------------------|------------------------------------------------------|
| Nombre, enlace de Discord, menú         | `web/src/config/site.ts`                             |
| Un servidor (texto, rates, mods…)       | `web/src/content/servidores/<slug>.md`               |
| Añadir un servidor                      | Nuevo `.md` en esa carpeta **y** su entrada en `api/servers.yaml` |
| Normas                                  | `web/src/content/normas/*.md`                        |
| Página Proyecto                         | `web/src/pages/proyecto.md`                          |
| Página Comunidad                        | `web/src/pages/comunidad.astro`                      |
| Colores y tipografías                   | `web/src/styles/base.css` (variables al principio)   |
| Imágenes                                | `web/public/img/` (usa .jpg o .webp, no .svg: Discord no muestra SVG en las vistas previas) |
| De dónde sale el estado de cada servidor| `api/servers.yaml`                                   |
| Datos de prueba del backend             | `api/mock/status.yaml`                               |
| Dirección pública de la web             | `web/astro.config.mjs` (`site`)                      |

El nombre del fichero de cada servidor (`the-island.md`) es su **slug**: aparece en la URL
(`/servidores/the-island/`) y es la clave en `api/servers.yaml`. Elígelo bien antes de publicar:
cambiarlo después rompe los enlaces compartidos.

---

## Fuentes de estado (backend)

Cada servidor puede tener varias fuentes en `api/servers.yaml`, por orden de prioridad:

| Fuente        | Qué sabe                                   | Estado                       |
|---------------|--------------------------------------------|------------------------------|
| `pterodactyl` | Si el proceso está encendido, arrancando…  | En uso (modo `live`)         |
| `ark_rcon`    | Jugadores conectados, desde el propio juego| En uso (solo red local)      |
| `mock`        | Datos de prueba                            | Solo para los tests          |

Reglas de combinación (`api/app/aggregator.py`):
- El estado lo da la primera fuente que responda (por eso Pterodactyl va primero).
- Jugadores y versión, de cualquier fuente que los tenga.
- Si ninguna responde → "Sin datos". Nunca se muestra "Offline" sin saberlo.
- `maintenance: true` en `servers.yaml` → "Mantenimiento".

Estados que ve el jugador: Online · Iniciando · Deteniéndose · Offline · Mantenimiento · Sin datos.

### Pterodactyl

1. Un usuario solo para el backend, añadido como subusuario de cada servidor con el permiso mínimo (`allocation.read`).
2. Con ese usuario, una clave de API de cliente.
3. En `api/.env`: `PTERODACTYL_MODE=live`, `PTERODACTYL_URL=...`, `PTERODACTYL_API_KEY=...`
4. En `api/servers.yaml`, el `server_id` de cada servidor (el identificador corto que sale en la URL del panel).

### RCON (jugadores conectados)

1. En cada servidor ARK: `RCONEnabled=True`, un `RCONPort` (el puerto asignado al servidor en Pterodactyl) y la `ServerAdminPassword`.
2. En `api/.env` (ver `api/.env.example`): `RCON_HOST`, `RCON_PASSWORD` y un `RCON_<SERVIDOR>_PORT` por servidor.
3. El puerto RCON **nunca** se abre a Internet. La API solo se conecta a direcciones de red local.

Si un servidor no responde por RCON, la web sigue mostrando su estado (de Pterodactyl) y los jugadores como "–".
El máximo de jugadores sale de `jugadoresMax` en la ficha de cada servidor.

### Para añadir otra fuente

Fichero nuevo en `api/app/sources/`, registrarlo en `api/app/sources/__init__.py` y usarlo en `servers.yaml`.
`api/app/sources/base.py` explica el formato.

---

## Seguridad

- `api/.env` nunca se sube a ningún repositorio (está en `.gitignore`).
- La API solo devuelve: estado, jugadores, máximo, versión y hora de consulta. Nunca IPs, IDs de Pterodactyl, CPU/RAM ni nombres de jugadores (hay un test que lo comprueba).
- RCON viaja sin cifrar: su puerto no debe abrirse a Internet; el backend debe llegar por red local o WireGuard.

## Fuera de esta fase

No hay base de datos, cuentas de usuario, tienda, pagos ni alquiler de servidores.
El contenido editorial vive en ficheros; una base de datos tendrá sentido cuando haga falta
editar desde un panel o guardar historial.
