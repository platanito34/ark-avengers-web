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
- Fuentes de estado en `api/app/sources/`: `pterodactyl` (modo simulated ahora; live cuando exista el panel), `ark_rcon` (preparada, sin implementar), `mock`.
- Hoy los servidores ARK funcionan en Windows Server; Pterodactyl aún no está instalado. No asumir que Pterodactyl es la única fuente.
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
- Todos los servidores, rates, mods, normas y textos actuales son DE EJEMPLO. No tratarlos como información real.
- No cambiar slugs sin avisar: forman parte de las URLs.

## Comandos
- Web: `cd web` → `npm install` (una vez) → `npm run dev` → http://localhost:4321
  - Escenarios de prueba: `?escenario=problemas | vacio | error`
- API: `cd api` → `pip install -r requirements.txt` → `uvicorn app.main:app --reload` → http://localhost:8000/docs
- Tests: `cd api && pytest`
- Windows: si PowerShell bloquea npm, usar `npm.cmd` o `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Próximos pasos previstos (no empezar sin que lo pida)
1. ~~Nombre centralizado en `site.ts`.~~ Hecho: ARK Avengers.
2. Revisar textos y datos reales de los servidores.
3. Implementar la fuente `ark_rcon` para los servidores actuales.
4. Conectar Pterodactyl (`PTERODACTYL_MODE=live`) cuando esté instalado.
5. Publicar la web estática y exponer la API de forma segura (sin abrir puertos de casa; p. ej. túnel).
