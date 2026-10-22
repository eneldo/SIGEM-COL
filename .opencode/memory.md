# SIGEM Colombia - Session Memory

## Project State (2026-10-21) - Auditoría integral + remediación completa

Tres fases cerradas: **(1)** auditoría RLS/multi-municipio con remediación P0/P1,
**(2)** tabla `auditoria_plataforma` + login multi-municipio sin `00000`,
**(3)** auditoría integral (backend/frontend/BD/infra/CI/QA/docs) con remediación completa
aplicada. Gates en verde: backend `525 passed / 0 failed` (+475 ERROR ambientales de BD),
ruff/format/mypy(87)/bandit limpios; frontend `477 passed`/build/lint; gitleaks **no leaks**
(allowlist por commit del hallazgo histórico); 3 compose validados; scripts shell `bash -n` OK.

**Estado: NO LISTO aún** — bloqueantes restantes: B-1 (flujo MFA en el SPA, sin pantalla de
setup/challenge) y operativos fuera del repo (aplicar migración 022, activar `sigem_app`,
rotar credencial BD si salió del entorno controlado). Todo el trabajo SIN COMITEAR (~57 archivos).

## Environment Facts (2026-10-21, Linux)

- **Ruta de trabajo**: `/mnt/DATOS/Proyectos/SIGEM-COL` (Linux/WSL mount; las rutas `F:\SIGEM-COL`
  de abajo son históricas de Windows).
- **BD host**: PostgreSQL 18.6 en `127.0.0.1:5432`; las credenciales `sigem`/`sigem_app` del
  `.env` NO funcionan contra esa BD (desconocidas) → 475 errores pytest ambientales; no se pudieron
  ejecutar checks contra BD viva ni `alembic upgrade` (regla del usuario: no ejecutar migraciones).
- **Docker**: socket con permission denied (sin sudo) → no se puede `docker compose up`; validar
  configs con `docker compose config` sí funciona.
- `.env` raíz contiene credenciales de dev (rol `sigem` superuser ⇒ RLS bypassado en dev actual);
  guardar "guardia con warning en dev" ya implementada en `core/database.py`.
- Gitleaks instalado localmente (`/usr/bin/gitleaks`); con `.gitleaks.toml` actual → 0 leaks.

## Key Facts

- **Stack**: Python 3.12 / FastAPI / SQLAlchemy 2.x async / PostgreSQL 17 / PyJWT / React 18 / TypeScript / Vite / Tailwind
- **Docker ports (dev)**: Backend 8001↔8000, Frontend 3001↔3000, PostgreSQL 5433, Redis 6379; desde
  2026-10-21 todos los puertos de gestión van enlazados a `127.0.0.1` (dev y local)
- Las credenciales administrativas no se documentan; se aprovisionan con secretos de entorno (`SIGEM_TEST_ADMIN_PASSWORD`/`SIGEM_BOOTSTRAP_PASSWORD`).
- **Tests API base**: `SIGEM_API_URL` opcional para tests in-process vs live
- **GitHub**: `https://github.com/eneldo/SIGEM-COL.git`, branch `master`
- **Rol de migración `sigem` en el PG local es SUPERUSER con BYPASSRLS**: ignora RLS. Cualquier
  prueba de aislamiento debe ejecutarse con un rol restringido (`tests/security/test_rls_isolation.py`
  crea `sigem_rls_test_app` equivalente a `sigem_app`; incluye `KNOWN_REVISIONS` hasta
  `022_auditoria_plataforma`).

## Critical Code Patterns

- `get_current_user_from_token` returns `{user, municipio_id, roles, permissions, sid}`. Access roles via `current_user["roles"]`, NOT `user.roles`
- RLS: la sesión de request es **una sola** (`get_db_with_rls = get_db`); `release_tenant_context()`
  hace RESET del GUC al devolver la conexión al pool; `assert_restricted_db_role()` falla en producción
  si el rol de conexión es superuser (CRITICAL log en dev)
- RBAC: `await require_permission(db, user.id, "permission.code")` — códigos normalizados a
  UPPER_SNAKE (`rbac._normalize_permission`); `reportes.py`/`cumplimiento.py` son authentication-only
  POR DISEÑO (ver decisions.md)
- **Login**: `LoginRequest.municipio_codigo` opcional; si falta y hay exactamente 1 municipio ACTIVO
  se resuelve; si hay varios → `ValueError("MUNICIPIO_REQUERIDO...")` → 422; nunca hardcodear
  `00000` ( nationale regla 1.2 de PROJECT_RULES)
- **Auditoría de plataforma**: eventos sin municipio → `AuditService.log_platform_event()` → tabla
  `auditoria_plataforma` (INSERT-only para `sigem_app`); eventos de tenant → `log_event()`
- Rate limiting: backend compartido (`core/rate_limit.py`), Redis en producción y memoria en dev; el bucket de login **falla cerrado** si Redis no responde (`RATE_LIMIT_FAIL_CLOSED_LOGIN`)
- **Sesión**: access token solo en memoria; refresh en cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth`; el refresh token nunca viaja en el cuerpo
- **JWT**: `TokenClaims` (Pydantic) valida `sub`/`municipio_id`/`type`/`exp`; claims inválidos → 401
- **MFA enforcement**: `MFA_ENFORCED_ROLES = ("ADMINISTRADOR_MUNICIPAL", "SUPERADMIN_PLATAFORMA")`; secretos TOTP cifrados AES-GCM (`enc:v1:`)
- Frontend: alias `@/*` **YA FUNCIONA** (corregido 2026-10-21 en vite.config.ts/tsconfig.json); lista
  de roles única en `src/lib/roles.ts` (`ADMIN_ROLES`, `GESTOR_ROUTE_ROLES`, …); routes `/admin`
  y `/gestor` con `requiredRole`
- **Evidencias**: firma magic bytes (`_valid_evidence_signature`), 10MB max, `resolve()`+contención
  del storage root, `municipio_id` siempre del token
- `datetime.now(UTC)` used in services (timezone-aware) para compatibilidad DB

## How to Run

```bash
# Tests backend (cambiar BD activa con credenciales válidas para los 475)
cd /mnt/DATOS/Proyectos/SIGEM-COL && src/backend/.venv/bin/pytest tests -c src/backend/pyproject.toml -q --no-cov

# Tests RLS (requieren BD migrada a head con rol sin BYPASSRLS)
python -m alembic upgrade head && python -m pytest tests/security/test_rls_isolation.py -q --no-cov

# Gates backend
cd /mnt/DATOS/Proyectos/SIGEM-COL && src/backend/.venv/bin/ruff check --config src/backend/pyproject.toml src/backend tests
cd src/backend && .venv/bin/mypy --config-file pyproject.toml .

# Tests frontend + gates
cd /mnt/DATOS/Proyectos/SIGEM-COL/src/frontend && npm run test && npm run build && npm run lint

# Gitleaks (como CI)
gitleaks detect --config .gitleaks.toml --redact

# Validar composés sin daemon
docker compose -f infra/docker/docker-compose.yml -p t config -q
SIGEM_IMAGE_TAG=sha-x SIGEM_DOMAIN=d.example docker compose -f infra/docker/docker-compose.prod.yml -p t config -q

# Prod (genera nginx.conf desde template con SIGEM_DOMAIN; requiere certs y 443 libre)
docker compose -f infra/docker/docker-compose.prod.yml --env-file infra/docker/.env.prod up -d
```

## Completed Work - Histórico (Hardening 2026-10-06; fases 1-3 ya completas en PROJECT_MEMORY.md)

### Credenciales expuestas
- Credencial administrativa que estaba versionada en `PROJECT_MEMORY.md`, `context/project_context.md`,
  `.opencode/memory.md`, `tests/conftest.py` y varios tests: **retirada**. Ahora los tests leen
  `SIGEM_TEST_ADMIN_PASSWORD` del entorno y las contraseñas temporales las genera un fixture.

### Backend
- MFA obligatorio también para `SUPERADMIN_PLATAFORMA` (`api/v1/auth.py:56`).
- Cifrado AES-GCM de secretos TOTP (`core/security.py`), `ENCRYPTION_KEY` validada en producción y
  distinta de `SECRET_KEY`/`JWT_SECRET_KEY`.
- Refresh token en cookie HttpOnly (`core/session_cookies.py`), defensa CSRF por validación de `Origin`.
- `TokenClaims` valida claims; `decode_token` devuelve `None` ante claims inválidos.
- Rate limiting distribuido con Redis (`core/rate_limit.py`, `core/redis_client.py`), degradación a
  memoria para tráfico general y fail-closed para login.
- Cabeceras: CSP, `Permissions-Policy`, `Cross-Origin-Opener-Policy`; retirada `X-XSS-Protection`.
- `hmac.compare_digest` para el token de métricas.
- `validate_production()` endurecido: algoritmo JWT, expiraciones, límites, cookie de sesión,
  `TRUST_PROXY_HEADERS` y coincidencia `SIGEM_APP_PASSWORD` ↔ `DATABASE_URL`.
- **`python-jose` → `pyjwt[crypto]`**: elimina `GHSA-3qf3-8w2g-rqmx` y `ecdsa 0.19.2`.

### Frontend
- Tokens fuera de `localStorage`: access en memoria, refresh en cookie; `withCredentials: true` y
  renovación transparente en 401 (`lib/api.ts`, `stores/authStore.ts`).
- `react-router-dom` actualizado a 7.x (cierra los advisories de open redirect).

### Infraestructura
- `infra/postgres/init/01-app-role.sh`: rol runtime sin `CREATE` sobre el esquema, solo DML,
  `NOSUPERUSER NOBYPASSRLS`.
- `infra/docker/backend/Dockerfile`: `uv sync --frozen --no-dev` (build reproducible) + `src/backend/uv.lock`.
- Imágenes fijadas sin `latest`.

### Pruebas nuevas
- `tests/backend/test_rate_limit_distributed.py` (backend Redis, ventanas, fail-closed)
- `tests/backend/test_refresh_cookie_security.py` (cookie HttpOnly, CSRF por Origin)
- `tests/backend/test_security_primitives_unit.py` (tokens, cifrado MFA, cabeceras)
- `tests/security/test_token_and_headers_security.py` (claims JWT, CORS efectivo, X-Request-ID, métricas)
- `tests/security/test_rls_isolation.py` (aislamiento real con rol sin BYPASSRLS)
- `src/frontend/src/lib/api.cookie.test.ts` (refresh por cookie)

## Bloqueantes vigentes

1. **B-1 · El frontend no tiene flujo de MFA**: el backend devuelve `mfa_required` + `mfa_token` en
   `/auth/login` y responde 403 `MFA_SETUP_REQUIRED`, pero no existe pantalla de setup/verify ni
   challenge de segundo factor, y el interceptor no maneja ese 403. Con MFA obligatorio para ambos
   roles privilegiados, una cuenta recién bootstrapeada queda sin forma de enrolarse y una con MFA
   activo entra en bucle 401 → refresh → login. **Hay que implementar la UI de MFA antes de desplegar.**
2. **B-2 · Gate de gitleaks: RESUELTO (2026-10-21)** — `.gitleaks.toml` ahora allowliste el commit
   histórico `abde3f3b…` (credencial de test ausente en HEAD); `gitleaks detect` local: no leaks.

## Acciones operativas fuera del repositorio

- Rotar la credencial que estuvo versionada y **purgar el historial Git** si el repositorio salió de
  un entorno controlado.
- Limpiar artefactos locales con credenciales: `.playwright-mcp/*.yml` y scripts raíz
  `check_*.py`/`test_backend.py`/`test_create_direct.py` — **HECHO 2026-10-21** (eliminados del
  disco; nunca estuvieron trackeados). Falta rotar la contraseña de BD expuesta si el repo de ellos
  salió de un entorno controlado.
- Recrear/reparar la base de datos de desarrollo si vuelve a desincronizarse (estuvo en 009 con
  columnas de 008; estaba en `020_personalizacion`; el head del código es `022_auditoria_plataforma`,
  migración aún NO aplicada) y luego activar `sigem_app` según el bloque SQL entregado.
- `infra/postgres/init/01-app-role.sh` solo corre con volumen nuevo: cambiar `SIGEM_APP_PASSWORD` en un
  entorno existente requiere actualizar el rol manualmente.
- Enrrolar MFA del administrador inicial tras el primer despliegue (no hay herramienta CLI; hoy solo
  existe la API).
