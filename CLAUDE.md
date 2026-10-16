# Proyecto: web pública de nuestros servidores de ARK: Survival Ascended

## Qué es
Web pública dedicada exclusivamente a nuestros servidores de ARK: Survival Ascended.
Tres pilares: **Servidores** (lista, estado en directo, fichas), **Proyecto** (quiénes somos) y **Comunidad** (Discord).
Quizá en el futuro haya otros juegos; de momento, solo ARK. No sobrediseñar para multijuego.

## Nombre
El nombre definitivo del proyecto es **ARK Avengers** (subtítulo: "Servidores de ARK: Survival Ascended").
Nombre y subtítulo salen de un único sitio: `web/src/config/site.ts` (`name` y `subtitle`). No escribirlos a mano en otras páginas.
En los ficheros Markdown se escribe `{nombre}` (en el texto y en `intro`/`nombreEnBuscador`) y se sustituye al generar la web.
- **Excepción con servidores reales:** cuando tengamos los servidores reales, `nombreEnBuscador` se escribe LITERAL en cada ficha (sin `{nombre}`), exactamente igual que el `SessionName` configurado en el servidor de ARK, porque es lo que el jugador busca en el juego.

## Arquitectura
```
Navegador → Web estática (web/, Astro) → API propia (api/, FastAPI) → Pterodactyl / juego (RCON) / mock
```
- La web NUNCA habla con Pterodactyl, su base de datos ni los servidores de juego. Solo con nuestra API.
- La API nunca expone: IPs, IDs de Pterodactyl, CPU/RAM, contraseñas, claves ni nombres de jugadores.
- Secretos solo en `api/.env` (nunca en el repositorio ni en `servers.yaml`).
- Contenido editorial (fichas, normas, textos) en ficheros Markdown dentro de `web/src/content/`. Sin base de datos de momento.
- Estado en directo: la API consulta las fuentes cada 30 s y guarda una caché; la web lee de la API.
- Infraestructura: Pterodactyl está instalado y conectado (`PTERODACTYL_MODE=live`). Los seis servidores ARK están en Pterodactyl (Wings en 192.168.1.101). La API corre en la misma red local (hoy en el ordenador del usuario; más adelante en una VM o Docker, también en la red local).
- Fuentes de estado en `api/app/sources/`, en este orden en `servers.yaml`:
  - `pterodactyl`: estado del proceso. Clave de cliente de un usuario subusuario de los seis servidores, solo con el permiso `allocation.read`. No pedir más permisos.
  - `ark_rcon`: jugadores conectados (`ListPlayers`). Solo se cuentan; los nombres nunca salen de la fuente. Host, puertos y contraseñas en `api/.env` (`RCON_HOST`, `RCON_PASSWORD`, `RCON_<SERVIDOR>_PORT`). Si falla, el estado sigue viniendo de Pterodactyl y los jugadores salen como "–".
  - `mock`: solo para los tests.
- RCON SOLO por red local: la fuente se niega a conectar con direcciones que no sean privadas. Nunca abrir el puerto RCON a Internet. Si la API sale de la red local, usar WireGuard.
- El máximo de jugadores sale de `jugadoresMax` en cada ficha (ni ListPlayers ni el permiso actual de Pterodactyl lo dan).
- Destacados de la portada: los 3 con más jugadores en ese momento; si nadie tiene jugadores (o no hay datos), primero los de `destacado: true`. Lo decide `web/src/scripts/live-status.ts`.
- Tests: no dependen de `api/.env` ni de servidores reales (`tests/conftest.py` fuerza el modo simulated; RCON se prueba con un servidor falso local).
- Estados públicos: online, starting, stopping, offline, maintenance, unknown. Si no se sabe, es `unknown`, nunca `offline`.

## Contrato web ↔ API
- `api/app/schemas.py` y `web/src/lib/status-types.ts` deben coincidir siempre.
- Los slugs (nombre del fichero en `web/src/content/servidores/`) deben coincidir con las claves de `api/servers.yaml`.
- Los tests (`cd api && pytest`) comprueban ambas cosas. Ejecutarlos después de cualquier cambio en el contrato o en los servidores.

## Diseño
- Mantener la estética actual: oscuro, verde basalto, ámbar para acciones, cian SOLO para datos en directo, esquinas cortadas, tipografías Big Shoulders Display + Barlow.
- Responsive (escritorio, tablet, móvil). Accesible (foco visible, contraste, `prefers-reduced-motion`).
- Variables de color y tipografía en `web/src/styles/base.css`.

## Idioma
- La web, los textos y los comentarios del código: en **castellano**.
- Conmigo puedes hablar en catalán o castellano.

## Reglas de trabajo
- NO implementar sin permiso explícito: tienda, pagos, cuentas de usuario, login, alquiler de servidores, gestión de clientes, base de datos.
- Antes de cambios grandes o de añadir dependencias, explicar el plan y esperar mi confirmación.
- No soy programador experto: explica los cambios paso a paso y en lenguaje sencillo.
- Los servidores, rates, normas y textos actuales son REALES. Lo marcado `PENDIENTE` o `PROVISIONAL` todavía no está decidido: no inventarlo.
- No cambiar slugs sin avisar: forman parte de las URLs.

## Comandos
- Web: `cd web` → `npm install` (una vez) → `npm run dev` → http://localhost:4321
  - Escenarios de prueba: `?escenario=problemas | sin-jugadores | vacio | error`
- API: `cd api` → `pip install -r requirements.txt` → `uvicorn app.main:app --reload` → http://localhost:8000/docs
- Tests: `cd api && pytest`
- Windows: si PowerShell bloquea npm, usar `npm.cmd` o `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Próximos pasos previstos (no empezar sin que lo pida)
1. ~~Nombre centralizado en `site.ts`.~~ Hecho: ARK Avengers.
2. ~~Revisar textos y datos reales de los servidores.~~ Hecho. Quedan estas preguntas abiertas (no inventar la respuesta):
   - Transferencias entre mapas: si se pueden pasar dinos, objetos y personajes, añadir a las fichas la característica "Transferencias de dinos, objetos y personajes entre los seis mapas".
   - Sanciones: qué pasa si alguien incumple las normas (aviso, expulsión temporal, ban).
   - (Resuelto) Mods: lista común en `web/src/content/mods.yaml`, mantenida a mano (ID, nombre y URL de CurseForge). La web la muestra en orden alfabético.
3. ~~Fuente `ark_rcon` para los jugadores conectados.~~ Hecho y probado con los servidores reales.
4. ~~Conectar Pterodactyl (`PTERODACTYL_MODE=live`).~~ Hecho.
5. Publicar la web estática y exponer la API de forma segura (sin abrir puertos de casa; p. ej. túnel).
