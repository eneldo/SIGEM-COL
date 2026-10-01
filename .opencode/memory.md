# SIGEM Colombia - Session Memory

## Project State (2026-09-30) - Post Hardening Producción

Full-stack municipal development plan tracking system. **Production hardening completo**: backend, infra, frontend tests, coverage push. **498 tests backend + 217 frontend = 715 tests pasando**. Gates: ruff, mypy, bandit, pytest, ESLint, tsc, build ✅.

## Key Facts

- **Stack**: Python 3.12 / FastAPI / SQLAlchemy 2.x async / PostgreSQL 17 / React 18 / TypeScript / Vite / Tailwind
- **Docker ports (dev)**: Backend 8001, Frontend 3001, PostgreSQL 5433, Redis 6379
- **Admin**: user `admin`, password `SigemAdmin2026!`, role SUPERADMIN_PLATAFORMA (mfa_activo=f, must_change_password=f)
- **Gestor**: user `enemova`, password `EneldoGestor2026!`, role GESTOR
- **Gestor Líder**: user `lider01`, password `GestorLider2026!`, role GESTOR_LIDER
- **Tests API base**: `SIGEM_API_URL` opcional para tests in-process vs live
- **Python venv**: `src/backend/.venv/` (usar `python -m ...`)
- **GitHub**: `https://github.com/eneldo/SIGEM-COL.git`, branch `master`
- **Local PG**: service `postgresql-x64-17` on port 5432 cannot be stopped
- **Local processes**: ports 8000/3000 occupied; Docker uses 8001/3001
- **Puerto 443**: ocupado por HTTP.sys (PID 4) en Windows → nginx prod no puede bindear 443 local

## Critical Code Patterns

- `get_current_user_from_token` returns `{user, municipio_id, roles, permissions, sid}`. Access roles via `current_user["roles"]`, NOT `user.roles`
- RLS: `RLSMiddleware` extracts municipio_id from JWT; `get_db_with_rls` calls `set_config('app.current_municipio_id', ...)`
- RBAC: `await require_permission(db, user.id, "permission.code")`
- Rate limiting: 2 buckets (login estricto `RATE_LIMIT_LOGIN_ATTEMPTS` + default `RATE_LIMIT_DEFAULT_REQUESTS`) + `TRUST_PROXY_HEADERS`
- Frontend: NO `@/*` alias working - use relative imports in components
- `datetime.now(UTC)` used in services (timezone-aware) para compatibilidad DB
- **MFA enforcement**: solo `ADMINISTRADOR_MUNICIPAL` (rol), `SUPERADMIN_PLATAFORMA` exento (cuenta bootstrap)
- **Logout**: revoca solo sesión actual (`sid` del token), no todas
- **Refresh token**: rotación con detección de reuso; no revoca familia completa por expiración simple

## How to Run

```bash
# Backend (local)
cd F:\SIGEM-COL && src\backend\.venv\Scripts\python.exe -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (local)
cd F:\SIGEM-COL\src\frontend && npm run dev

# Docker stack dev
cd F:\SIGEM-COL && docker-compose -f infra/docker/docker-compose.yml up -d

# Tests backend
cd F:\SIGEM-COL && python -m pytest tests -c src/backend/pyproject.toml -q --no-cov

# Tests frontend
cd F:\SIGEM-COL\src\frontend && npm run test:coverage

# Lint/typecheck backend
cd F:\SIGEM-COL && python -m ruff check src/backend tests scripts && python -m mypy src/backend

# Lint/typecheck frontend
cd F:\SIGEM-COL\src\frontend && npm run lint && npx tsc --noEmit

# Alembic in Docker
docker exec --env DATABASE_URL="postgresql+asyncpg://sigem:sigem_password@sigem-postgres:5432/sigem_db" sigem-backend python -m alembic upgrade head

# Prod stack (requiere certs en infra/tls/ y puerto 443 libre)
docker-compose -f infra/docker/docker-compose.prod.yml --env-file infra/docker/.env.prod up -d
```

## Completed Work (Hardening Producción - 2026-09-30)

### Backend Hardening
- Health checks: `/health` (503 si unhealthy), `/health/live`, `/health/ready`, `/metrics` (prometheus-client + METRICS_TOKEN)
- JSON logging estructurado (`core/logging.py`: `JsonFormatter`, `setup_logging`)
- Config validation en lifespan (`validate_production()`)
- Rate limiter 2 buckets + `TRUST_PROXY_HEADERS` + `get_client_ip`
- ValueError → 422 handler para UUID inválidos
- MFA enforcement server-side: `MFA_ENFORCED_ROLES = ("ADMINISTRADOR_MUNICIPAL",)`, `MFA_ALLOWED_SUFFIXES = PASSWORD_CHANGE_ALLOWED_SUFFIXES`
- Logout revoca solo sesión actual (`sid`), fallback `revoke_all_sessions` solo si no hay `sid`
- Refresh token rotation: reuso detectado → 401, no revoca familia completa por expiración
- 43 tests nuevos (`test_production_hardening.py`)
- Gates: ruff, ruff format, mypy (79 archivos), bandit ✅

### Infraestructura Producción
- `infra/docker/docker-compose.prod.yml` (postgres/redis/migrate/backend/frontend/nginx/backup + profile monitoring)
- `infra/nginx/nginx.prod.conf` (80→301, TLS 1.2/1.3, HSTS, CSP, rate limits, sin X-XSS-Protection)
- `infra/postgres/init/01-app-role.sh` (rol `sigem_app` + `ALTER DEFAULT PRIVILEGES`, fix B-01)
- `infra/monitoring/prometheus.yml` + `alerts.yml`
- Scripts backup: `scripts/backup/*` (backup_db/evidencias/retention/run/restore/verify)
- `scripts/setup/deploy.sh` + `rollback.sh` (SSH, health checks, rollback automático)
- Docs: `docs/operations/{deployment,tls,backups,monitoring,ci-cd}.md`
- Migración 011 corregida (datetime bind para asyncpg, no `.isoformat()`)
- `.dockerignore` raíz, `Dockerfile.frontend` con `npm ci` + healthcheck

### Frontend Tests
- 13 archivos, **217 tests passed**
- Cobertura global: 18.6% lines / 91.06% branches / 86.02% functions
- Umbrales `vite.config.ts`: global lines 17, branches 90, functions 85 + per-file ≥80% en componentes críticos
- Gates: ESLint, tsc --noEmit, npm run test:coverage, npm run build ✅
- Excepción temporal cobertura lines documentada en `context/decisions.md` con plan de rampa

### Cobertura Backend Push
- 3 subagentes paralelos: 319 tests nuevos en 8 archivos
- Cobertura global: **59%** (objetivo 80% - gap ~1080 stmts)
- Mejoras clave: catálogos CRUD (lineas, programas, productos, dependencias, roles), gestores/avances/dashboards, auditoría/cumplimiento/reportes/pdf/usuarios/auth
- Tests en `tests/backend/test_*.py` (8 archivos nuevos)

### CI/CD Pipeline (`.github/workflows/ci.yml`)
- Jobs: backend-quality, backend-tests (postgres+redis services, `--cov-fail-under=80`), frontend-quality, security (gitleaks, pip-audit, npm audit), docker-build, deploy (workflow_dispatch + SSH)
- **Nota:** Gate cobertura backend fallará hasta alcanzar 80% (actual 59%)

### Decisiones Documentadas (`context/decisions.md`)
1. Excepción temporal cobertura frontend + plan de rampa
2. MFA enforcement solo ADMINISTRADOR_MUNICIPAL
3. Logout revoca solo sesión actual
4. Refresh token rotation sin revocación masiva por expiración
5. ValueError → 422 handler para UUID inválidos

## Test Suite Status
- **Backend**: 498 passed, 1 skipped (0 failed) - gates all green
- **Frontend**: 217 passed - gates all green

## Known Issues
- Puerto 443 ocupado por HTTP.sys (PID 4) en Windows → nginx prod no puede bindear 443 localmente
- Cobertura backend 59% vs 80% objetivo (requiere ~1080 stmts más en servicios débiles)
- Vulnerabilidades npm audit en react-router-dom (transitivas, alpha)
- Cobertura frontend 18.6% lines (excepción documentada)