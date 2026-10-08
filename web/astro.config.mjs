// Configuración de Astro: https://docs.astro.build/es/reference/configuration-reference/
import { defineConfig } from "astro/config";

export default defineConfig({
  // Dirección pública definitiva de la web. Se usa para las vistas previas
  // de Discord/redes (las imágenes necesitan la URL completa). Cámbiala al publicar.
  site: "https://ark.cazamojitos.example",

  // /servidores/ en vez de /servidores.html
  trailingSlash: "ignore",
  build: { format: "directory" },
});
