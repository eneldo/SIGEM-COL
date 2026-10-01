# TLS — Certificados HTTPS en producción

**Propósito:** el bloque auditado B-02 (sin TLS) se resuelve con `infra/nginx/nginx.prod.conf`, que escucha 443 con certificados montados desde `infra/tls/` (solo lectura: `../tls:/etc/nginx/tls:ro`).

Archivos requeridos en `infra/tls/`:

| Archivo | Contenido |
|---|---|
| `fullchain.pem` | certificado (+ cadena intermedia si aplica) |
| `privkey.pem` | clave privada |

`infra/tls/.gitignore` excluye todo salvo sí mismo: **ningún certificado ni clave se commitea jamás**.

---

## 1. Certificado de desarrollo (self-signed)

```bash
bash scripts/setup/generate_dev_cert.sh
```

El script usa `docker run --rm -v <ruta>:/certs alpine/openssl req -x509 ...` (no requiere openssl en el host; en este equipo no hay openssl instalado, por eso se prefiere Docker). Si no hay Docker pero sí openssl en el PATH, usa el openssl del host. Genera `fullchain.pem` y `privkey.pem` con `CN=localhost` y `subjectAltName=DNS:localhost,IP:127.0.0.1`, válidos 365 días.

Útil para `nginx -t`, despliegues internos y smoke tests. El navegador mostrará advertencia de certificado no confiable.

---

## 2. Certificado de producción con certbot (Let's Encrypt)

Requisitos: dominio público apuntando al servidor, puertos 80/443 accesibles desde Internet.

### Opción A — standalone (recomendada en primer despliegue)

```bash
docker run --rm \
  -p 80:80 -p 443:443 \
  -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/lib/letsencrypt:/var/lib/letsencrypt \
  certbot/certbot certonly --standalone \
  -d Dominio.Com \
  --agree-tos -m tu-correo@example.com --non-interactive
```

> Si el stack SIGEM ya está levantado, nginx ocupa el 80/443: para el primer certificado levante el stack con `docker compose ... up -d` **sin** el servicio nginx o detenga nginx temporalmente, emita el certificado y vuelva a levantar.

### Opción B — webroot (renovaciones sin detener nginx)

El stack publica 80 → `http-01` puede validarse contra un volumen webroot compartido. Con `nginx.prod.conf` en modo redirect, añada temporalmente un location `/.well-known/acme-challenge/` apuntando al webroot o emita el certificado con el desafío alojado manualmente.

### Instalación de certificados en infra/tls

Certbot escribe en `/etc/letsencrypt/live/<dominio>/`. Copie (o enlace) al directorio que nginx consume:

```bash
sudo cp /etc/letsencrypt/live/<dominio>/fullchain.pem infra/tls/fullchain.pem
sudo cp /etc/letsencrypt/live/<dominio>/privkey.pem   infra/tls/privkey.pem
sudo chmod 644 infra/tls/fullchain.pem
sudo chmod 600 infra/tls/privkey.pem
sudo chown root:root infra/tls/*.pem
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec nginx nginx -s reload
```

### Renovación automática

```bash
sudo certbot renew --post-hook "cp /etc/letsencrypt/live/<dominio>/fullchain.pem /ruta/al/repo/infra/tls/fullchain.pem && cp /etc/letsencrypt/live/<dominio>/privkey.pem /ruta/al/repo/infra/tls/privkey.pem && docker compose -f /ruta/al/repo/infra/docker/docker-compose.prod.yml -p sigem-prod exec nginx nginx -s reload"
```

Certbot instala un timer de systemd (`certbot.timer`) que ejecuta la renovación dos veces al día; el `--post-hook` copia los archivos y recarga nginx sin reiniciar el contenedor. Verifique con `sudo systemctl status certbot.timer`.

---

## 3. Verificación

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec nginx nginx -t
echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -dates -subject
```

Parámetros activos en `nginx.prod.conf`: `TLSv1.2` + `TLSv1.3`, HSTS `max-age=63072000; includeSubDomains`, `server_tokens off`. No se configura OCSP stapling porque el contenedor no declara un resolver DNS explícito; añádalo solo si lo necesita y tiene un resolver disponible.
