# SIGEM Colombia - Session Memory

## Project State (2026-09-22)

Full-stack municipal development plan tracking system. Docker deployed, RBAC working, 76 tests passing.

## Key Facts

- **Stack**: Python 3.12 / FastAPI / SQLAlchemy async / PostgreSQL 17 / React / TypeScript / Vite / Tailwind
- **Docker ports**: Backend 8001, Frontend 3001, PostgreSQL 5433, Redis internal
- **Admin**: user `admin`, password `SigemAdmin2026!`, role SUPERADMIN_PLATAFORMA
- **Gestor**: user `candresmejia`, password `@aTrfh0xcHYKng*QOkyDshUr`, role GESTOR_LIDER
- **Python venv**: `src/backend/.venv/`
- **GitHub**: `https://github.com/eneldo/SIGEM-COL.git`, branch `master`
- **Local PG**: service `postgresql-x64-17` on port 5432 cannot be stopped
- **Local processes**: ports 8000/3000 occupied; Docker uses 8001/3001

## Critical Code Patterns

- `get_current_user_from_token` returns `{user, municipio_id, roles, permissions}`. Access roles via `current_user["roles"]`, NOT `user.roles`
- RLS: `RLSMiddleware` extracts municipio_id from JWT; `get_db_with_rls` calls `set_config('app.current_municipio_id', ...)`
- RBAC: `await require_permission(db, user.id, "permission.code")`
- Rate limiter: in-memory, 2000 req/15min (RATE_LIMIT_LOGIN_ATTEMPTS=200)
- Frontend: NO `@/*` alias working - use relative imports in components
- `datetime.utcnow()` used in services (not timezone-aware) for DB compatibility

## How to Run

```bash
# Backend (local)
cd F:\SIGEM-COL && src\backend\.venv\Scripts\python.exe -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (local)
cd F:\SIGEM-COL\src\frontend && npm run dev

# Docker stack
cd F:\SIGEM-COL && docker-compose -f infra/docker/docker-compose.yml up -d

# Tests
cd F:\SIGEM-COL && src\backend\.venv\Scripts\python.exe -m pytest tests/ -v

# Alembic in Docker
docker exec --env DATABASE_URL="postgresql+asyncpg://sigem:sigem_password@sigem-postgres:5432/sigem_db" sigem-backend python -m alembic upgrade head
```

## Completed Work

### Security (CRIT-01 to CRIT-07)
- RLS activated on all multi-municipality tables
- Non-root Docker containers
- Secret management via env_file
- HTTPS nginx config for production
- RBAC real in dashboards
- PostgreSQL not exposed externally
- Redis authenticated

### Docker Deployment
- Full stack: backend + frontend + PostgreSQL + Redis
- Alembic migrations working in container
- 9 users seeded (admin, superadmin, 7 gestores)
- Health checks on all services

### Test Suite (76 tests)
- 16 auth tests (login, tokens, logout, password change)
- 7 user CRUD tests
- 12 dashboard + RBAC tests
- 8 integration tests (health, catalogos, full workflow)
- 33 security tests (SQL injection, XSS, auth bypass, headers)

## Known Issues

- `candresmejia` was locked (intentos_fallidos=5) in local DB - reset to 0
- gestor dashboard route is `/api/v1/gestor/dashboard/...` (not `/gestor-dashboard/`)
- `UsuarioCreate` requires `codigo` field (not optional)
- Soft delete on users returns 500 in some cases (delete endpoint issue)
- Invalid UUID format returns 500 instead of 400/422
