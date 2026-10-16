/**
 * CLIENTE DE ESTADO
 * Es el ÚNICO sitio de la web que pide el estado de los servidores.
 *
 *   PUBLIC_STATUS_SOURCE=fixtures -> usa fixtures/status/*.json (sin backend)
 *   PUBLIC_STATUS_SOURCE=api      -> llama a PUBLIC_API_URL/api/status
 *
 * Valores por defecto (si no hay web/.env):
 *   - Producción (npm run build): API real, con ruta relativa "/api/status".
 *     La web y la API están bajo el mismo dominio (Caddy envía /api/* a la API).
 *   - Desarrollo (npm run dev): datos de prueba y API en http://localhost:8000.
 *
 * La web nunca habla con Pterodactyl ni con los servidores de juego:
 * solo con nuestro backend.
 */
import type { StatusResponse } from "./status-types";

const PROD = import.meta.env.PROD;
const SOURCE = import.meta.env.PUBLIC_STATUS_SOURCE || (PROD ? "api" : "fixtures");
const API_URL = (import.meta.env.PUBLIC_API_URL ?? (PROD ? "" : "http://localhost:8000")).replace(/\/$/, "");
const DEFAULT_FIXTURE = import.meta.env.PUBLIC_STATUS_FIXTURE ?? "normal";

const fixtures = import.meta.glob<StatusResponse>("../../fixtures/status/*.json", {
  eager: true,
  import: "default",
});

async function fromFixtures(): Promise<StatusResponse> {
  // Permite probar escenarios desde el navegador: ?escenario=problemas
  const name = new URLSearchParams(location.search).get("escenario") ?? DEFAULT_FIXTURE;
  await new Promise((r) => setTimeout(r, 350)); // simula la espera de una API real

  if (name === "error") throw new Error("Error simulado (escenario=error)");
  const data = fixtures[`../../fixtures/status/${name}.json`];
  if (!data) throw new Error(`No existe el escenario "${name}"`);

  // Los ficheros tienen fechas fijas; las ponemos a "ahora" para que se vea realista
  const now = new Date().toISOString();
  return {
    generated_at: now,
    servers: data.servers.map((s) => ({ ...s, checked_at: s.checked_at ? now : null })),
  };
}

async function fromApi(): Promise<StatusResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(`${API_URL}/api/status`, { signal: controller.signal });
    if (!res.ok) throw new Error(`La API respondió ${res.status}`);
    return (await res.json()) as StatusResponse;
  } finally {
    clearTimeout(timer);
  }
}

export function fetchStatus(): Promise<StatusResponse> {
  return SOURCE === "api" ? fromApi() : fromFixtures();
}
