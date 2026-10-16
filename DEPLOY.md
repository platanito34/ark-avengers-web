# Publicar ARK Avengers

```
Internet ──► Router (80/443) ──► Raspberry Pi: Caddy (HTTPS, arkavengers.duckdns.org)
                                       │
                                       ├── /api/*  ──► 192.168.1.101:<PUERTO_API>  Servidor Pterodactyl "API" (Python)
                                       └── resto   ──► 192.168.1.101:<PUERTO_WEB>  Servidor Pterodactyl "Web" (Node.js)
```

- Todo va bajo el mismo dominio: la web llama a la API con la ruta relativa `/api/status`.
- Solo los puertos **80 y 443** se abren en el router, y solo hacia la Raspberry (Caddy).
  Los puertos de la API, de la web, del panel y de RCON **nunca** se abren en el router.
- La documentación interactiva de la API (`/docs`) no queda publicada: Caddy solo envía `/api/*` a la API.

---

## 0. Antes de empezar

### Token de GitHub (el repositorio es privado)

Los dos servidores descargan el código de GitHub con un token de **solo lectura**:

1. GitHub (cuenta `platanito34`) → *Settings* → *Developer settings* → *Personal access tokens* → **Fine-grained tokens** → *Generate new token*.
2. *Repository access*: **Only select repositories** → `ark-avengers-web`.
3. *Permissions* → *Repository permissions* → **Contents: Read-only**. Nada más.
4. Ponle caducidad (p. ej. 1 año) y apúntate la fecha: cuando caduque, hay que generar otro y cambiarlo en los dos servidores.

El token se guarda dentro de cada servidor de Pterodactyl. No lo pongas en ningún fichero del repositorio.

### Eggs

Se usan los eggs genéricos de la comunidad (repositorio `pelican-eggs/generic` en GitHub):

| Servidor | Fichero del egg |
|----------|-----------------|
| API      | `python/egg-pterodactyl-python-generic.json` |
| Web      | `nodejs/egg-pterodactyl-nodejs-generic.json` |

1. Descarga los dos `.json` (botón *Download raw file* en GitHub).
2. Panel → *Admin* → *Nests* → *Import Egg* → elige el fichero y un nest (p. ej. uno nuevo llamado "Web").
3. **Importante:** estos eggs vienen con un texto de arranque de ejemplo y, sin cambiarlo, el servidor se
   queda para siempre en "Starting". En *Admin* → *Nests* → (egg) → pestaña *Configuration* → **Start Configuration**:

   | Egg     | Start Configuration |
   |---------|---------------------|
   | Python  | `{"done": ["Application startup complete"]}` |
   | Node.js | `{"done": ["Web lista en el puerto"]}` |

### Puertos (allocations)

Cada servidor necesita **un** puerto en el nodo `192.168.1.101`. Cualquiera libre sirve; por ejemplo:

| Servidor | Puerto de ejemplo | Quién se conecta |
|----------|-------------------|------------------|
| API      | `8100`            | Solo Caddy (Raspberry) |
| Web      | `8101`            | Solo Caddy (Raspberry) |

*Admin* → *Nodes* → (nodo) → *Allocation* → IP `192.168.1.101`, puertos `8100, 8101`.
No los redirijas en el router.

> Wings usa Docker, y Docker se salta `ufw`: una regla de `ufw` en Ubuntu **no** bloquea estos puertos.
> Lo que los protege es que el router no los redirige. Compruébalo en el paso 5.

---

## 1. Servidor "API" (Python)

*Admin* → *Servers* → *Create New*:

| Campo | Valor |
|-------|-------|
| Egg | Python generic |
| Docker image | Python 3.12 (o 3.13) |
| Memoria | **512 MB** (en marcha usa ~50-100 MB; mínimo 256 MB) |
| Disco | 1 GB |
| CPU | 50 % es suficiente |
| Allocation | `192.168.1.101:8100` (el puerto de la API) |

Variables:

| Variable | Valor |
|----------|-------|
| Git Repo Address | `https://github.com/platanito34/ark-avengers-web` |
| Git Branch | `main` |
| Git Username | `platanito34` |
| Git Access Token | el token del paso 0 |
| Auto Update | `1` (al reiniciar descarga la última versión) |
| User Uploaded Files | `0` |
| App py file | `api/run.py` |
| Requirements file | `api/requirements.txt` |

Cuando termine la instalación (descarga el repositorio):

1. *Files* → carpeta `api/` → *New File* → `.env`. Copia el contenido de `api/.env.example` y rellénalo:
   ```
   CORS_ORIGINS=https://arkavengers.duckdns.org
   PTERODACTYL_MODE=live
   PTERODACTYL_URL=http://192.168.1.101        ← la dirección del panel
   PTERODACTYL_API_KEY=ptlc_...                ← la clave de cliente
   RCON_HOST=192.168.1.101
   RCON_PASSWORD=...
   RCON_GENESIS_1_PORT=...                     ← y el resto de puertos RCON
   ```
   Este fichero no está en GitHub (`.gitignore`) y `git pull` no lo toca.
2. *Start*. En la consola debe salir `Application startup complete` y el servidor pasar a "Running".
3. Desde un ordenador de casa: `http://192.168.1.101:8100/api/status` debe devolver los seis servidores.
   Si salen todos como `unknown`, mira la consola: dirá si falla el panel o RCON.

> `run.py` arranca la API sin `--reload`, en `0.0.0.0`, en el puerto de Pterodactyl y con un solo proceso
> (la caché y la consulta cada 30 s tienen que existir una sola vez).

---

## 2. Servidor "Web" (Node.js)

*Admin* → *Servers* → *Create New*:

| Campo | Valor |
|-------|-------|
| Egg | Node.js generic |
| Docker image | Nodejs 22 (o 24) |
| Memoria | **1536 MB** (la compilación es lo que más usa: ~400 MB medidos, más npm; mínimo 1024 MB) |
| Disco | 2 GB (ocupa ~150 MB, pero `npm ci` necesita margen) |
| CPU | 100 % (la compilación tarda menos) |
| Allocation | `192.168.1.101:8101` (el puerto de la web) |

Variables:

| Variable | Valor |
|----------|-------|
| Main file | `web/start.js` |
| Git Repo Address | `https://github.com/platanito34/ark-avengers-web` |
| Install Branch | `main` |
| Git Username | `platanito34` |
| Git Access Token | el token del paso 0 |
| Auto Update | `1` |
| User Uploaded Files | `0` |
| Additional Node packages / Uninstall / Arguments | vacíos |

*Start*. Cada arranque hace, en este orden (lo verás en la consola):

1. `npm ci` — instala exactamente las versiones de `web/package-lock.json`.
2. `npm run build` — compila la web en `web/dist/` (1-2 minutos la primera vez).
3. Sirve `web/dist/` y escribe `[web] Web lista en el puerto 8101`.

Desde un ordenador de casa: `http://192.168.1.101:8101` debe mostrar la web.
(Ahí el estado dice que no se puede consultar: es normal, la ruta `/api/status` solo existe a través de Caddy.)

**Dirección pública:** las vistas previas de Discord usan `https://arkavengers.duckdns.org` (está en
`web/astro.config.mjs`). Si algún día cambia el dominio, o lo cambias ahí, o creas en el egg una variable
`SITE_URL` con la nueva dirección.

---

## 3. Caddy (Raspberry Pi)

Añade al `Caddyfile` (normalmente `/etc/caddy/Caddyfile`). Los valores entre `{$...:...}` son variables
con su valor por defecto: si cambian el dominio o los puertos, basta con definirlas en el entorno de Caddy.

```caddy
{$ARK_DOMAIN:arkavengers.duckdns.org} {
	encode zstd gzip

	# API: solo las rutas /api/* (la documentación /docs NO se publica)
	handle /api/* {
		reverse_proxy {$ARK_API:192.168.1.101:8100}
	}

	# Todo lo demás: la web
	handle {
		reverse_proxy {$ARK_WEB:192.168.1.101:8101}
	}

	header {
		Strict-Transport-Security "max-age=31536000"
		-Server
	}
}
```

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Caddy obtiene y renueva solo el certificado HTTPS (necesita los puertos 80 y 443 abiertos hacia la Raspberry).

### DuckDNS

La IP de casa puede cambiar. Si aún no tienes un actualizador en la Raspberry:

```bash
# crontab -e   (cada 5 minutos; TU_TOKEN_DUCKDNS sale en duckdns.org)
*/5 * * * * curl -s "https://www.duckdns.org/update?domains=arkavengers&token=TU_TOKEN_DUCKDNS&ip=" >/dev/null
```

---

## 4. Actualizar la web o la API

1. Sube los cambios a GitHub (`git push`).
2. Panel → servidor → *Restart*. Con *Auto Update* = `1`, descarga la última versión antes de arrancar.
   La web se vuelve a compilar sola; la API reinstala los paquetes si han cambiado.

---

## 5. Comprobaciones finales

Con el móvil **sin wifi** (datos móviles), para probar desde fuera de casa:

- [ ] `https://arkavengers.duckdns.org` carga con candado (HTTPS) y el estado de los servidores sale en directo.
- [ ] `https://arkavengers.duckdns.org/api/status` devuelve JSON con los seis servidores.
- [ ] `https://arkavengers.duckdns.org/docs` da la página 404 de la web (la documentación no es pública).
- [ ] `http://<tu IP pública>:8100` y `:8101` **no** responden (los puertos internos están cerrados).
- [ ] Una ficha de servidor compartida en Discord muestra la imagen en la vista previa.

## Problemas frecuentes

| Síntoma | Causa probable |
|---------|----------------|
| El servidor se queda en "Starting" | Falta cambiar la *Start Configuration* del egg (paso 0). |
| La instalación falla con "Repository not found" | Token caducado, sin permiso sobre este repositorio o usuario equivocado. |
| La web se reinicia durante `npm run build` | Poca memoria: sube la del servidor Web. |
| `/api/status` da todo `unknown` | Revisa `api/.env` y la consola de la API (panel o RCON). |
| Error 502 en el dominio | Caddy no llega al puerto: servidor apagado o puerto distinto en el Caddyfile. |
