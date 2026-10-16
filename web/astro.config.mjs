// Configuración de Astro: https://docs.astro.build/es/reference/configuration-reference/
import { defineConfig } from "astro/config";
import { remarkNombre } from "./src/lib/remark-nombre";

export default defineConfig({
  // Dirección pública de la web. Se usa para las vistas previas de Discord/redes
  // (las imágenes necesitan la URL completa). Se puede cambiar sin tocar el código
  // con la variable de entorno SITE_URL (p. ej. en el servidor de Pterodactyl).
  site: process.env.SITE_URL || "https://arkavengers.duckdns.org",

  // /servidores/ en vez de /servidores.html
  trailingSlash: "ignore",
  build: { format: "directory" },

  // {nombre} en el texto de los .md → nombre del proyecto (src/config/site.ts)
  markdown: { remarkPlugins: [remarkNombre] },
});
