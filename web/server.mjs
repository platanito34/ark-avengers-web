/**
 * SERVIDOR DE PRODUCCIÓN DE LA WEB
 * ================================
 * Sirve los ficheros ya compilados de dist/ (sin dependencias: solo Node).
 * Lo arranca start.js en Pterodactyl. Para probarlo en local:
 *     npm run build  →  node server.mjs  →  http://localhost:8080
 *
 * - Puerto: SERVER_PORT (lo asigna Pterodactyl), si no PORT, si no 8080.
 * - /servidores y /servidores/ → dist/servidores/index.html
 * - Si no existe → dist/404.html con código 404.
 * - Nunca sirve nada fuera de dist/ (protección contra rutas con "../").
 * - La compresión (gzip/zstd) y el HTTPS los pone Caddy, delante.
 */
import { createReadStream } from "node:fs";
import { stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath } from "node:url";

const DIST = fileURLToPath(new URL("./dist/", import.meta.url));
const PORT = Number(process.env.SERVER_PORT || process.env.PORT || 8080);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".avif": "image/avif",
  ".gif": "image/gif",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
};

const SECURITY_HEADERS = {
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Frame-Options": "DENY",
};

/** Cuánto puede guardar el navegador cada tipo de fichero */
function cacheControl(urlPath, ext) {
  if (urlPath.startsWith("/_astro/")) return "public, max-age=31536000, immutable"; // nombre con hash
  if (ext === ".html") return "no-cache"; // siempre comprobar si hay versión nueva
  return "public, max-age=86400"; // imágenes, favicon...: un día
}

async function fileAt(path) {
  try {
    const info = await stat(path);
    return info.isFile() ? info : null;
  } catch {
    return null;
  }
}

/** Traduce la URL a un fichero de dist/, o null si no existe */
async function resolveFile(urlPath) {
  let decoded;
  try {
    decoded = decodeURIComponent(urlPath);
  } catch {
    return null;
  }
  const full = normalize(join(DIST, decoded));
  if (!full.startsWith(DIST.endsWith(sep) ? DIST : DIST + sep)) return null; // fuera de dist/

  const candidates = decoded.endsWith("/")
    ? [join(full, "index.html")]
    : [full, join(full, "index.html")];
  for (const path of candidates) {
    const info = await fileAt(path);
    if (info) return { path, info };
  }
  return null;
}

function send(req, res, status, file, urlPath) {
  const ext = extname(file.path).toLowerCase();
  res.writeHead(status, {
    ...SECURITY_HEADERS,
    "Content-Type": MIME[ext] ?? "application/octet-stream",
    "Content-Length": file.info.size,
    "Cache-Control": status === 200 ? cacheControl(urlPath, ext) : "no-cache",
    "Last-Modified": file.info.mtime.toUTCString(),
  });
  if (req.method === "HEAD") return res.end();
  createReadStream(file.path).pipe(res);
}

const server = createServer(async (req, res) => {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { ...SECURITY_HEADERS, Allow: "GET, HEAD" }).end();
    return;
  }
  const urlPath = new URL(req.url ?? "/", "http://localhost").pathname;
  try {
    const file = await resolveFile(urlPath);
    if (file) return send(req, res, 200, file, urlPath);

    const notFound = await resolveFile("/404.html");
    if (notFound) return send(req, res, 404, notFound, urlPath);
    res.writeHead(404, { ...SECURITY_HEADERS, "Content-Type": "text/plain; charset=utf-8" }).end("No encontrado");
  } catch (err) {
    console.error("[web] error sirviendo", urlPath, err);
    if (!res.headersSent) res.writeHead(500).end();
    else res.destroy();
  }
});

server.listen(PORT, "0.0.0.0", () => {
  // Pterodactyl usa este texto para saber que el servidor ya está en marcha
  console.log(`[web] Web lista en el puerto ${PORT}`);
});
