# Despliegue — Runbook de producción

Stack productivo: `infra/docker/docker-compose.prod.yml` con proyecto `sigem-prod`.

> El stack de **desarrollo no cambia**: sigue siendo `infra/docker/docker-compose.yml` (puertos 8001/3001/5433, proyecto por defecto). No mezcle volúmenes ni proyectos: producción usa `sigem-prod_*` y desarrollo usa `docker_*`.

## 1. Topología

| Servicio | Imagen | Puertos | Rol |
|---|---|---|---|
| `nginx` | `nginx:alpine` | **80, 443 (único publicado)** | TLS, SPA, proxy `/api/`, `/uploads/`, `/health` |
| `frontend` | `sigem-frontend:<tag>` | ninguno | SPA Vite servida por nginx (interno) |
| `backend` | `sigem-backend:<tag>` | ninguno | FastAPI/uvicorn (interno) |
| `migrate` | `sigem-backend:<tag>` | ninguno | one-shot: `alembic upgrade head` como rol `sigem` |
| `postgres` | `postgres:17-alpine` | ninguno | datos + init de rol `sigem_app` (B-01) |
| `redis` | `redis:7-alpine` | ninguno | caché con contraseña, appendonly |
| `backup` | `sigem-backup:<tag>` | ninguno | respaldo diario al volumen `backups` |
| `prometheus` | `prom/prometheus` | 127.0.0.1:9090 | perfil `monitoring` (opcional) |

Redes: `sigem_internal` (todo) y `sigem_public` (solo nginx). Imágenes etiquetadas con `SIGEM_IMAGE_TAG` (default `latest`) para que CI fije SHA/tag.

Orden de arranque: `postgres` healthy → `migrate` completa → `backend` healthy → `frontend` healthy → `nginx`.

## 2. Primer despliegue (host vacío)

```bash
# 1. Entorno
cp infra/docker/.env.prod.example infra/docker/.env.prod
$EDITOR infra/docker/.env.prod
```

Genere cada secreto por separado con `openssl rand -base64 48` (para valores dentro de URLs use `openssl rand -hex 32` o URL-encode). Reemplace `CHANGE_ME.example` por el dominio real en `FRONTEND_URL`, `BACKEND_URL` y `CORS_ORIGINS`. **`SIGEM_APP_PASSWORD` debe coincidir con la contraseña dentro de `DATABASE_URL`.**

```bash
# 2. TLS (desarrollo/self-signed o certificado real: docs/operations/tls.md)
bash scripts/setup/generate_dev_cert.sh

# 3. Despliegue con tag inmutable
bash scripts/setup/deploy.sh v1.0.0
```

`deploy.sh` hace: verifica `.env.prod` y certificados → obtiene/builda las imágenes del tag → `docker compose up -d` (ejecuta `migrate` automáticamente vía `depends_on: service_completed_successfully`) → espera salud → smoke checks (API, SPA y `/health` a través de nginx TLS). Si algo falla, imprime instrucciones de rollback y sale con código ≠ 0.

Equivalente manual sin el script:

```bash
export SIGEM_IMAGE_TAG=v1.0.0
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod build
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod up -d
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod ps
```

Verificación del primer despliegue:

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod logs migrate
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec postgres psql -U sigem -d sigem_db -c "\du sigem_app"
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec nginx wget -q --no-check-certificate -O - https://127.0.0.1/health
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod exec backup /backup/verify_backup.sh 2>/dev/null || true
```

Cree el administrador inicial con `scripts/setup/bootstrap_admin.py` (ejecutar dentro del contenedor backend, ver su cabecera).

## 3. Despliegue rutinario (nueva versión)

```bash
bash scripts/setup/deploy.sh <tag-nuevo>
```

Si el tag no existe localmente, intenta `pull` y si no, `build` con ese tag. Las migraciones corren siempre (one-shot `migrate`); si falla, `up` aborta y el backend no se reinicia con schema incompatible.

## 4. Rollback

```bash
bash scripts/setup/rollback.sh <tag-anterior>
```

El rollback **es redeplegar el tag anterior de imagen**. El script NO ejecuta `alembic downgrade` (es destructivo). Si la release fallida ya aplicó migraciones, además restaure la BD desde el respaldo más reciente (`docs/operations/backups.md` §4) y luego levante el tag anterior. El script imprime estos pasos en cada ejecución.

## 5. Checklist post-despliegue

- [ ] `docker compose ... ps` → todos `healthy` (nginx, backend, frontend, postgres, redis) y `migrate` `Exited (0)`.
- [ ] `logs migrate` sin errores y con la revisión esperada.
- [ ] `https://<dominio>/` devuelve la SPA (200, sin errores de CSP en consola).
- [ ] `https://<dominio>/health` → `"status": "healthy"`.
- [ ] Login funcional y una consulta de listado con datos de dos municipios distintos (aislamiento RLS).
- [ ] Cabeceras: `Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, sin `X-XSS-Protection` (ver `curl -k -I https://.../`).
- [ ] `docker compose ... exec backup /backup/verify_backup.sh` → `verification passed`.
- [ ] Logs sin errores 5xx sostenidos: `docker compose ... logs --tail=100 backend`.
- [ ] Con perfil `monitoring`: `up{job="sigem-backend"} == 1` en la UI de Prometheus.

## 6. Operación frecuente

```bash
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod logs -f backend nginx
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod run --rm migrate      # re-ejecutar migraciones
docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod --profile monitoring up -d   # activar Prometheus
```

Windows (PowerShell): los scripts son bash; ejecute `bash scripts/setup/deploy.sh <tag>` (Git for Windows) o use los comandos `docker compose` directamente.

## 7. Seguridad operativa

- `infra/docker/.env.prod` está en `.gitignore`; nunca se commitea ni se copia a imágenes.
- Backend, postgres y redis no publican puertos; solo nginx recibe tráfico externo.
- El rol de la aplicación es `sigem_app` (no superuser) para que RLS aplique; las migraciones corren como `sigem` mediante `ALEMBIC_DATABASE_URL`.

## 8. Despliegue desde CI/CD

El runbook manual de las secciones 1-7 sigue siendo la vía principal y siempre disponible. Adicionalmente, `.github/workflows/ci.yml` expone el job `deploy`, que ejecuta exactamente el mismo flujo en el host de producción de forma remota.

### 8.1. Disparo

- **Solo** `workflow_dispatch` (Actions → CI → Run workflow) con el input `deploy_tag` (tag inmutable, p. ej. `v1.0.0`).
- En `push` y `pull_request` a `master` el job queda *skipped*: **ningún push despliega**.
- Corre únicamente si los gates `backend-quality`, `backend-tests`, `frontend-quality` y `security` terminaron verdes (`needs`).

### 8.2. Secretos requeridos

| Secreto | Valor |
|---|---|
| `DEPLOY_HOST` | dominio o IP del servidor |
| `DEPLOY_USER` | usuario SSH con permisos de `docker compose` en `DEPLOY_PATH` |
| `DEPLOY_PATH` | ruta absoluta del clon del repo en el servidor |
| `SSH_PRIVATE_KEY` | clave privada sin passphrase (la pública va en `authorized_keys`) |

Si falta alguno, el job **falla con un mensaje explícito** (`Missing required GitHub secrets: ...`) en lugar de saltarse en silencio. Procedimiento de generación de la clave: `docs/operations/ci-cd.md` §5.

### 8.3. Qué ejecuta

```bash
cd "$DEPLOY_PATH"
bash scripts/setup/deploy.sh "$deploy_tag"
```

Es el mismo script del runbook manual: verifica `.env.prod` y certificados → obtiene/builda las imágenes del tag → `docker compose -f infra/docker/docker-compose.prod.yml -p sigem-prod up -d` (migraciones *one-shot*) → espera salud → smoke checks sobre nginx TLS. Ante un fallo sale con código ≠ 0 y el paso del job queda en rojo.

### 8.4. Después del despliegue desde CI

Completar el checklist de la §5. El rollback es siempre manual: `bash scripts/setup/deploy.sh <tag-anterior>` en el host (§4), no existe job automático de rollback.

Detalle completo del pipeline, gates y umbrales: [ci-cd.md](ci-cd.md).
