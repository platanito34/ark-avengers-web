/**
 * CONFIGURACIÓN GENERAL DE LA WEB
 * Nombre, enlace de Discord y menú: se cambian aquí y afectan a todas las páginas.
 */
export const site = {
  // Es el único sitio donde se escribe el nombre del proyecto.
  // En los ficheros Markdown no se escribe a mano: se pone {nombre} y se sustituye solo.
  name: "ARK Avengers",
  // Aparece bajo el título grande de la portada y en el título de la pestaña de inicio
  subtitle: "Servidores de ARK: Survival Ascended",
  description:
    "Servidores de ARK: Survival Ascended con estado en directo, configuración clara y una comunidad activa en Discord.",

  discordUrl: "https://discord.gg/gfJsBTgYm",

  nav: [
    { label: "Inicio", href: "/" },
    { label: "Servidores", href: "/servidores/" },
    { label: "Proyecto", href: "/proyecto/" },
    { label: "Comunidad", href: "/comunidad/" },
    { label: "Normas", href: "/normas/" },
  ],

  // Imagen por defecto para las vistas previas en Discord y redes (jpg/png, no svg)
  ogImage: "/img/hero.jpg",
};

/** Sustituye {nombre} por el nombre del proyecto (para textos escritos en Markdown). */
export function conNombre(texto: string): string {
  return texto.replaceAll("{nombre}", site.name);
}
