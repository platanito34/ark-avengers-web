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
 *   data-featured="3"               destacados de la portada (ver renderFeatured)
 *     data-destacados="a,b"         slugs con `destacado: true`, por orden
 *     data-order="a,b,c..."         todos los slugs, en el orden de las fichas
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

/**
 * Destacados de la portada. Se muestran `count` tarjetas:
 *   1. primero, las que tienen jugadores conectados, de más a menos;
 *   2. después (o si nadie tiene jugadores, o no hay datos), las `destacado: true`;
 *   3. si aún faltan, el resto por el orden de las fichas.
 * En caso de empate manda el orden de las fichas.
 */
function chooseFeatured(slugs: string[], destacados: string[], count: number, bySlug: Map<string, ServerStatus>) {
  const playersOf = (slug: string) => {
    const s = bySlug.get(slug);
    return s?.state === "online" ? s.players.current ?? 0 : 0;
  };
  const withPlayers = slugs.filter((s) => playersOf(s) > 0).sort((a, b) => playersOf(b) - playersOf(a));
  return [...new Set([...withPlayers, ...destacados, ...slugs])].slice(0, count);
}

function renderFeatured(grid: HTMLElement, bySlug: Map<string, ServerStatus>) {
  const cards = [...grid.querySelectorAll<HTMLElement>(":scope > [data-live-slug]")];
  const slugs = (grid.dataset.order ?? "").split(",").filter(Boolean); // orden de las fichas
  const destacados = (grid.dataset.destacados ?? "").split(",").filter(Boolean);
  const chosen = chooseFeatured(slugs, destacados, Number(grid.dataset.featured) || 3, bySlug);

  const bySlugCard = new Map(cards.map((c) => [c.dataset.liveSlug!, c]));
  for (const slug of [...chosen, ...slugs.filter((s) => !chosen.includes(s))]) {
    const card = bySlugCard.get(slug);
    if (!card) continue;
    card.hidden = !chosen.includes(slug);
    grid.append(card); // append mueve la tarjeta al final: así quedan en el orden elegido
  }
}

function renderError() {
  document.querySelectorAll<HTMLElement>("[data-featured]").forEach((g) => renderFeatured(g, new Map()));
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
    document.querySelectorAll<HTMLElement>("[data-featured]").forEach((g) => renderFeatured(g, bySlug));
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
