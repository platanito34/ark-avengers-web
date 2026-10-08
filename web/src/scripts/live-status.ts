/**
 * ESTADO EN DIRECTO
 * La página llega con el contenido ya escrito (nombre, mapa, rates...).
 * Este script solo rellena los huecos de datos en directo y los refresca cada minuto.
 *
 * Huecos que entiende (atributos en el HTML):
 *   data-live-slug="<slug>"         contenedor de un servidor (tarjeta o ficha)
 *     data-live="chip"              etiqueta de estado
 *     data-live="players"           "38 / 70"
 *     data-live="players-bar"       barra de ocupación
 *     data-live="version"           versión del juego
 *     data-live="checked"           "Actualizado hace..."
 *   data-live-summary               panel de resumen de la portada
 *     data-summary="online|players|updated"
 */
import { fetchStatus } from "../lib/status-client";
import { STATE_LABELS, type PublicState, type ServerStatus } from "../lib/status-types";

const REFRESH_MS = 60_000;
const fmt = (n: number) => n.toLocaleString("es-ES");

function timeAgo(iso: string | null): string {
  if (!iso) return "Sin datos recientes";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "Actualizado hace unos segundos";
  const m = Math.round(s / 60);
  if (m < 60) return `Actualizado hace ${m} ${m === 1 ? "minuto" : "minutos"}`;
  const h = Math.round(m / 60);
  return `Actualizado hace ${h} ${h === 1 ? "hora" : "horas"}`;
}

function setChip(el: Element | null, state: PublicState | "pending") {
  if (!el) return;
  el.setAttribute("data-state", state);
  el.textContent = STATE_LABELS[state];
}

function renderServer(container: HTMLElement, status: ServerStatus | undefined) {
  const state: PublicState = status?.state ?? "unknown";
  const online = state === "online";
  // El máximo anunciado en la ficha sirve de respaldo si el backend no lo da
  const max = status?.players.max ?? (Number(container.dataset.maxPlayers) || null);
  const current = online ? status?.players.current ?? null : null;

  container.dataset.state = state;
  setChip(container.querySelector('[data-live="chip"]'), state);

  const players = container.querySelector('[data-live="players"]');
  if (players) {
    players.innerHTML = current === null
      ? `<strong>–</strong> / ${max ? fmt(max) : "–"}`
      : `<strong>${fmt(current)}</strong> / ${max ? fmt(max) : "–"}`;
  }

  const bar = container.querySelector<HTMLElement>('[data-live="players-bar"]');
  if (bar) bar.style.width = current !== null && max ? `${Math.min(100, (current / max) * 100)}%` : "0";

  const version = container.querySelector('[data-live="version"]');
  if (version) version.textContent = online && status?.version ? status.version : "–";

  const checked = container.querySelector('[data-live="checked"]');
  if (checked) checked.textContent = timeAgo(status?.checked_at ?? null);
}

function renderSummary(panel: HTMLElement, bySlug: Map<string, ServerStatus>) {
  const slugs = (panel.dataset.slugs ?? "").split(",").filter(Boolean);
  const statuses = slugs.map((s) => bySlug.get(s)).filter((s): s is ServerStatus => !!s);
  const online = statuses.filter((s) => s.state === "online");
  const players = online.reduce((sum, s) => sum + (s.players.current ?? 0), 0);
  const latest = statuses.map((s) => s.checked_at).filter(Boolean).sort().pop() ?? null;

  panel.querySelector('[data-summary="online"]')!.textContent = fmt(online.length);
  panel.querySelector('[data-summary="players"]')!.textContent = fmt(players);
  panel.querySelector('[data-summary="updated"]')!.textContent = timeAgo(latest);
  panel.classList.remove("is-loading", "is-error");
}

function renderError() {
  document.querySelectorAll<HTMLElement>("[data-live-slug]").forEach((c) => renderServer(c, undefined));
  document.querySelectorAll<HTMLElement>("[data-live-summary]").forEach((panel) => {
    panel.classList.remove("is-loading");
    panel.classList.add("is-error");
    panel.querySelector('[data-summary="updated"]')!.textContent =
      "Ahora mismo no podemos consultar el estado. Lo volveremos a intentar en un minuto.";
  });
}

async function refresh() {
  try {
    const data = await fetchStatus();
    const bySlug = new Map(data.servers.map((s) => [s.slug, s]));
    document.querySelectorAll<HTMLElement>("[data-live-slug]").forEach((c) => renderServer(c, bySlug.get(c.dataset.liveSlug!)));
    document.querySelectorAll<HTMLElement>("[data-live-summary]").forEach((p) => renderSummary(p, bySlug));
  } catch (err) {
    console.warn("[estado]", err);
    renderError();
  }
}

export function startLiveStatus() {
  if (!document.querySelector("[data-live-slug], [data-live-summary]")) return;
  refresh();
  setInterval(() => {
    if (document.visibilityState === "visible") refresh();
  }, REFRESH_MS);
}
