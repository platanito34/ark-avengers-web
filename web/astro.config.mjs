// Configuración de Astro: https://docs.astro.build/es/reference/configuration-reference/
import { defineConfig } from "astro/config";
import { remarkNombre } from "./src/lib/remark-nombre";

export default defineConfig({
  // Dirección pública definitiva de la web. Se usa para las vistas previas
  // de Discord/redes (las imágenes necesitan la URL completa). Cámbiala al publicar.
  site: "https://example.com",

  // /servidores/ en vez de /servidores.html
  trailingSlash: "ignore",
  build: { format: "directory" },

  // {nombre} en el texto de los .md → nombre del proyecto (src/config/site.ts)
  markdown: { remarkPlugins: [remarkNombre] },
});
