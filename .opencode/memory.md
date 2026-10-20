# SIGEM Colombia - Session Memory

## Project State (2026-10-06) - Hardening de seguridad previo a producción

Full-stack municipal development plan tracking system. Se cerró la auditoría de
preparación de producción: **575 tests backend (100 % cobertura) + 480 frontend**,
gates ruff/mypy/bandit/pytest/eslint/tsc/build en verde y **0 vulnerabilidades**
en dependencias de producción (backend y frontend).

**Estado: NO LISTO aún** por dos bloqueantes identificados en la reauditoría (ver abajo).

## Key Facts

- **Stack**: Python 3.12 / FastAPI / SQLAlchemy 2.x async / PostgreSQL 17 / PyJWT / React 18 / TypeScript / Vite / Tailwind
- **Docker ports (dev)**: Backend 8001, Frontend 3001, PostgreSQL 5433, Redis 6379
- Las credenciales administrativas y de gestores no se documentan; se aprovisionan y suministran mediante secretos de entorno (`SIGEM_TEST_ADMIN_PASSWORD`).
- **Tests API base**: `SIGEM_API_URL` opcional para tests in-process vs live
- **GitHub**: `https://github.com/eneldo/SIGEM-COL.git`, branch `master`
- **Local PG**: service `postgresql-x64-17` on port 5432 cannot be stopped
- **Local processes**: ports 8000/3000 occupied; Docker uses 8001/3001
- **Puerto 443**: ocupado por HTTP.sys (PID 4) en Windows → nginx prod no puede bindear 443 local
- **Rol de migración `sigem` en el PG local es SUPERUSER con BYPASSRLS**: ignora RLS. Cualquier
  prueba de aislamiento debe ejecutarse con un rol restringido (`tests/security/test_rls_isolation.py`
  crea `sigem_rls_test_app` equivalente a `sigem_app`).

## Critical Code Patterns

- `get_current_user_from_token` returns `{user, municipio_id, roles, permissions, sid}`. Access roles via `current_user["roles"]`, NOT `user.roles`
- RLS: `RLSMiddleware` extracts municipio_id from JWT; `get_db`/`get_db_with_rls` call `set_config('app.current_municipio_id', ...)` con conexión dedicada por request
- RBAC: `await require_permission(db, user.id, "permission.code")`
- Rate limiting: backend compartido (`core/rate_limit.py`), Redis en producción y memoria en dev; dos ventanas (general `RATE_LIMIT_WINDOW`, login `RATE_LIMIT_LOGIN_WINDOW_MINUTES*60`); el bucket de login **falla cerrado** si Redis no responde (`RATE_LIMIT_FAIL_CLOSED_LOGIN`)
- **Sesión**: access token solo en memoria; refresh token en cookie `HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth`; `POST /auth/refresh` valida `Origin` contra `CORS_ORIGINS`; el refresh token ya **no** viaja en el cuerpo
- **JWT**: `TokenClaims` (Pydantic) valida `sub`/`municipio_id`/`type`/`exp` en `decode_token`; claims inválidos → 401 (nunca 500)
- **MFA enforcement**: `MFA_ENFORCED_ROLES = ("ADMINISTRADOR_MUNICIPAL", "SUPERADMIN_PLATAFORMA")`
- **MFA en reposo**: secretos TOTP cifrados con AES-GCM (`enc:v1:`) usando `ENCRYPTION_KEY`; formato legado en claro aún aceptado (migración oportunista)
- Frontend: NO `@/*` alias working - use relative imports in components
- `datetime.now(UTC)` used in services (timezone-aware) para compatibilidad DB

## How to Run

```bash
# Backend (local)
cd F:\SIGEM-COL && python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (local)
cd F:\SIGEM-COL\src\frontend && npm run dev

# Docker stack dev
cd F:\SIGEM-COL && docker-compose -f infra/docker/docker-compose.yml up -d

# Tests backend (gate de CI: 100 % cobertura)
cd F:\SIGEM-COL && python -m pytest tests -c src/backend/pyproject.toml -q --no-cov

# Cobertura exacta como en CI
cd F:\SIGEM-COL && python -m pytest tests --cov=src/backend --cov-report=xml --cov-fail-under=100

# Tests que necesitan BD migrada a head
cd F:\SIGEM-COL && python -m alembic upgrade head
cd F:\SIGEM-COL && python -m pytest tests/security/test_rls_isolation.py -q --no-cov

# Tests frontend
cd F:\SIGEM-COL\src\frontend && npm run test:coverage

# Lint/typecheck backend
cd F:\SIGEM-COL && python -m ruff check src/backend tests && python -m mypy src/backend

# Lint/typecheck frontend
cd F:\SIGEM-COL\src\frontend && npm run lint && npx tsc --noEmit

# Auditoría reproducible de dependencias de producción (backend)
cd F:\SIGEM-COL && uv export --format requirements-txt --no-dev --no-emit-project --directory src/backend --output-file /tmp/sigem-req.txt
cd F:\SIGEM-COL && python -m pip_audit -r /tmp/sigem-req.txt --strict

# Gitleaks (historial completo, como CI)
docker run --rm -v "${PWD}:/repo" -w /repo zricethezav/gitleaks:latest detect --source . --config .gitleaks.toml

# Prod stack (requiere certs en infra/tls/ y puerto 443 libre)
docker-compose -f infra/docker/docker-compose.prod.yml --env-file infra/docker/.env.prod up -d
```

## Completed Work (Hardening de seguridad - 2026-10-06)

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

## BLOQUEANTES PENDIENTES (2026-10-06)

1. **B-1 · El frontend no tiene flujo de MFA**: el backend devuelve `mfa_required` + `mfa_token` en
   `/auth/login` y responde 403 `MFA_SETUP_REQUIRED`, pero no existe pantalla de setup/verify ni
   challenge de segundo factor, y el interceptor no maneja ese 403. Con MFA obligatorio para ambos
   roles privilegiados, una cuenta recién bootstrapeada queda sin forma de enrolarse y una con MFA
   activo entra en bucle 401 → refresh → login. **Hay que implementar la UI de MFA antes de desplegar.**
2. **B-2 · Gate de gitleaks**: corregido `regexTarget = "secret"` y el literal `ClaveSegura123` del
   test; quedan 2 avisos en el **historial** (commit `abde3f3`) que requieren allowlist o purga.

## Acciones operativas fuera del repositorio

- Rotar la credencial que estuvo versionada y **purgar el historial Git** si el repositorio salió de
  un entorno controlado.
- Limpiar artefactos locales no versionados que contienen credenciales: `.playwright-mcp/*.yml` y
  scripts raíz `check_*.py` con contraseñas de `sigem`/`sigem_app`.
- Recrear/reparar la base de datos de desarrollo si vuelve a desincronizarse (estuvo en 009 con
  columnas de 008; ya está en `020_personalizacion`).
- `infra/postgres/init/01-app-role.sh` solo corre con volumen nuevo: cambiar `SIGEM_APP_PASSWORD` en un
  entorno existente requiere actualizar el rol manualmente.
- Enrrolar MFA del administrador inicial tras el primer despliegue (no hay herramienta CLI; hoy solo
  existe la API).
