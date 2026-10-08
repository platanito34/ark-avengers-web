/**
 * CONFIGURACIÓN GENERAL DE LA WEB
 * Nombre, enlace de Discord y menú: se cambian aquí y afectan a todas las páginas.
 */
export const site = {
  name: "Cazamojitos",
  description:
    "Servidores de ARK: Survival Ascended con estado en directo, configuración clara y una comunidad activa en Discord.",

  // Sustitúyelo por la invitación real
  discordUrl: "https://discord.gg/TU-CODIGO",

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
