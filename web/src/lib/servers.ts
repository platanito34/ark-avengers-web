/** Lectura de las fichas de servidores (contenido editorial) */
import { getCollection, type CollectionEntry } from "astro:content";

export type Server = CollectionEntry<"servidores">;

/** Servidores visibles, ordenados por el campo `orden` */
export async function getVisibleServers(): Promise<Server[]> {
  const all = await getCollection("servidores", (s) => s.data.visible);
  return all.sort((a, b) => a.data.orden - b.data.orden || a.data.mapa.localeCompare(b.data.mapa));
}

export async function getFeaturedServers(limit = 3): Promise<Server[]> {
  return (await getVisibleServers()).filter((s) => s.data.destacado).slice(0, limit);
}

export const RATE_LABELS = [
  ["xp", "XP"],
  ["doma", "Doma"],
  ["recoleccion", "Recolección"],
  ["cria", "Cría"],
] as const;
