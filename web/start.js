/**
 * ARRANQUE DE PRODUCCIÓN DE LA WEB (Pterodactyl)
 * ==============================================
 * Lo usa el egg genérico de Node.js con MAIN_FILE=web/start.js.
 * En cada arranque:
 *   1. npm ci          instala exactamente las versiones de package-lock.json
 *   2. npm run build   compila la web en dist/ (la parte que más memoria usa)
 *   3. server.mjs      sirve dist/ en el puerto de Pterodactyl
 *
 * Variables de entorno:
 *   SITE_URL     dirección pública (por defecto https://arkavengers.duckdns.org)
 *   SERVER_PORT  la pone Pterodactyl
 */
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const WEB_DIR = fileURLToPath(new URL(".", import.meta.url));
const env = { ...process.env, ASTRO_TELEMETRY_DISABLED: "1" };

function run(command) {
  console.log(`[web] > ${command}`);
  execSync(command, { cwd: WEB_DIR, stdio: "inherit", env });
}

run("npm ci --no-audit --no-fund");
run("npm run build");
await import("./server.mjs");
