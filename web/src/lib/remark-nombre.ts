/**
 * Sustituye {nombre} por el nombre del proyecto (site.ts) en el texto de
 * todos los ficheros Markdown: fichas de servidores, normas, proyecto.md…
 * Se activa en astro.config.mjs.
 */
import { conNombre } from "../config/site";

interface Nodo {
  type: string;
  value?: string;
  children?: Nodo[];
}

function recorrer(nodo: Nodo) {
  if (nodo.type === "text" && nodo.value) nodo.value = conNombre(nodo.value);
  nodo.children?.forEach(recorrer);
}

export function remarkNombre() {
  return (arbol: Nodo) => recorrer(arbol);
}
