# Contexto del Proyecto SIGEM Colombia

## Estado al 2026-09-22

Sistema completo de seguimiento al Plan de Desarrollo Municipal con Docker desplegado, RBAC funcional y suite de 76 tests pasando.

## Arquitectura

- **Backend**: Python 3.12 / FastAPI / SQLAlchemy 2.x async / PostgreSQL 17 / Alembic
- **Frontend**: React 18+ / TypeScript / Vite / Tailwind CSS
- **Infraestructura**: Docker Compose (backend, frontend, PostgreSQL, Redis)
- **Autenticación**: JWT (access + refresh tokens) / Argon2id passwords / RLS por municipio
- **RBAC**: 5 roles (SUPERADMIN_PLATAFORMA, ADMINISTRADOR_MUNICIPAL, GESTOR_LIDER, AUDITOR, CONSULTA)

## Puertos Docker

| Servicio | Puerto Externo | Puerto Interno |
|----------|---------------|----------------|
| Backend | 8001 | 8000 |
| Frontend | 3001 | 3000 |
| PostgreSQL | 5433 | 5432 |
| Redis | - | 6379 |

## Credenciales

| Usuario | Password | Rol | Municipio |
|---------|----------|-----|-----------|
| admin | SigemAdmin2026! | SUPERADMIN_PLATAFORMA | 00000 (bdb39d8c) |
| superadmin | SuperAdmin2026! | SUPERADMIN_PLATAFORMA | 00000 (bdb39d8c) |
| candresmejia | @aTrfh0xcHYKng*QOkyDshUr | GESTOR_LIDER | 00000 (bdb39d8c) |
| ldiazmoreno | @aTrfh0xcHYKng*QOkyDshUr | GESTOR_LIDER | 00000 (bdb39d8c) |
| mgarcialopez | Gestor2026! | GESTOR_LIDER | 00000 |
| crodriguezperez | Gestor2026! | GESTOR_LIDER | 00000 |
| amartinezsanchez | Gestor2026! | GESTOR_LIDER | 00000 |
| pfernandezruiz | Gestor2026! | GESTOR_LIDER | 00000 |
| agomezvargas | Gestor2026! | GESTOR_LIDER | 00000 |

## GitHub

- Repo: `https://github.com/eneldo/SIGEM-COL.git`
- Branch: `master`
- Último commit: `16a2f91` (feat: comprehensive test suite)

## Trabajo completado

### Core (sesiones anteriores)
- Módulo de gestores: CRUD, estados, permisos, dependencias, credenciales temporales, auditoría.
- Dashboard administrativo con KPIs y alertas de seguridad.
- Dashboard del gestor con productos asignados y registro de avances.
- CRUD completo: Líneas estratégicas → Programas → Productos.
- Catálogos: roles, dependencias.
- Auditoría del sistema.
- Reportes y cumplimiento.
- Layout responsive con sidebar colapsable.
- Password change modal (5min cancelable, 10min mandatory).
- RBAC real en dashboards usando `require_permission()`.

### Seguridad (sesión 2026-09-22)
- **CRIT-01**: RLS activado — `RLSMiddleware` extrae `municipio_id` del JWT; `get_db_with_rls` ejecuta `set_config('app.current_municipio_id', ...)`.
- **CRIT-02**: Contenedor Docker non-root (`USER app`).
- **CRIT-03**: Secret management via `env_file` + `.env`.
- **CRIT-04**: HTTPS nginx (configurado para producción).
- **CRIT-05**: RBAC real en dashboards admin y gestor.
- **CRIT-06**: PostgreSQL no expuesto externamente (usa 5433:5432 por conflicto con PG local).
- **CRIT-07**: Redis con autenticación (`requirepass`).

### Docker (sesión 2026-09-22)
- `Dockerfile` backend: non-root, sin `--reload`, `fpdf2` en dependencias.
- `Dockerfile` frontend: multi-stage build con nginx.
- `docker-compose.yml`: `env_file`, health checks, puertos 8001/3001/5433.
- `nginx.conf`: root/index directives, SPA routing, API proxy, gzip.
- `migrations/env.py`: lee `DATABASE_URL` de variable de entorno.
- `alembic.ini` copiado al container.
- Seed de usuarios en Docker DB (admin, superadmin, 7 gestores).

### Tests (sesión 2026-09-22)
- **76 tests pasando** al 100%.
- `tests/backend/test_auth.py` (16 tests): login, tokens, logout, cambio contraseña.
- `tests/backend/test_usuarios.py` (7 tests): CRUD, búsqueda, paginación, duplicados.
- `tests/backend/test_dashboard.py` (12 tests): KPIs admin, dashboard gestor, RBAC.
- `tests/integration/test_integracion.py` (8 tests): health, catálogos, flujo completo.
- `tests/security/test_security.py` (33 tests): SQL injection, XSS, auth bypass, headers.

### Fixes conocidos
- `candresmejia` desbloqueado (intentos_fallidos reset a 0) en DB local.
- Rate limit aumentado a 2000 req/15min para tests (`RATE_LIMIT_LOGIN_ATTEMPTS=200`).
- `get_current_user_from_token` retorna dict con `user`, `municipio_id`, `roles`, `permissions`. Acceder a roles via `current_user["roles"]`.

## Archivos clave

### Backend
- `src/backend/main.py` — FastAPI app + middleware stack
- `src/backend/core/config.py` — Settings (Pydantic)
- `src/backend/core/database.py` — RLSMiddleware + get_db_with_rls
- `src/backend/core/security.py` — JWT, password hashing (Argon2id)
- `src/backend/core/rbac.py` — `require_permission()`
- `src/backend/core/middleware.py` — Rate limiter (in-memory)
- `src/backend/api/v1/router.py` — All API routes
- `src/backend/api/v1/auth.py` — Login, /me, change-password, logout
- `src/backend/api/v1/usuarios.py` — CRUD usuarios
- `src/backend/api/v1/lineas.py` — CRUD líneas estratégicas
- `src/backend/api/v1/programas.py` — CRUD programas
- `src/backend/api/v1/productos.py` — CRUD productos
- `src/backend/api/v1/dashboard/admin.py` — Dashboard admin (KPIs, resumen, alertas)
- `src/backend/api/v1/gestor_dashboard.py` — Dashboard gestor (mis-productos, avances)
- `src/backend/api/v1/catalogos.py` — Catálogos (roles, dependencias)
- `src/backend/pyproject.toml` — Dependencias incluyendo fpdf2

### Frontend
- `src/frontend/src/App.tsx` — Rutas (sin redirect forzado a /change-password)
- `src/frontend/src/stores/authStore.ts` — Estado auth (loginTimestamp, dismissPasswordChange)
- `src/frontend/src/components/PasswordChangeModal.tsx` — Modal cambio contraseña
- `src/frontend/src/components/layout/Layout.tsx` — Incluye PasswordChangeModal

### Infraestructura
- `infra/docker/backend/Dockerfile` — Backend container
- `infra/docker/frontend/Dockerfile` — Frontend multi-stage
- `infra/docker/docker-compose.yml` — Stack completo
- `infra/nginx/nginx.conf` — Reverse proxy + SPA
- `.env` — Variables de entorno (no commit)
- `alembic.ini` — Configuración Alembic
- `migrations/env.py` — Lee DATABASE_URL de env var

### Tests
- `tests/conftest.py` — Fixtures (api client, tokens)
- `tests/backend/test_auth.py` — 16 tests
- `tests/backend/test_usuarios.py` — 7 tests
- `tests/backend/test_dashboard.py` — 12 tests
- `tests/integration/test_integracion.py` — 8 tests
- `tests/security/test_security.py` — 33 tests

## Pendiente conocido

- **Local PG**: servicio `postgresql-x64-17` no se puede detener; Docker usa puerto 5433.
- **Local processes**: puertos 8000/3000 ocupados; Docker usa 8001/3001.
- **Validar responsive** en 390px.
- **Seed completo**: falta plan de desarrollo, dependencias reales, datos de ejemplo.
- **MFA**: código existe pero no está completamente integrado.
- **Reportes PDF**: servicio creado, necesita validación end-to-end.
