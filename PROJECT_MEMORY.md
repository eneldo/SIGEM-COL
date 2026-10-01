# SIGEM Colombia - Project Memory

## Estado Actual (2026-09-30) - Post Hardening Producción

### Commits Recientes (pendientes de push)
- Hardening producción completo: backend, infra, frontend tests, coverage push
- Fixes MFA enforcement, logout, refresh token, UUID validation
- Documentación decisions.md con excepciones y decisiones técnicas

### Estado de Funcionalidades

#### Autenticación y Autorización
- Login: usuario + contraseña + municipio_codigo
- MFA TOTP obligatorio para **ADMINISTRADOR_MUNICIPAL** (rol), exento SUPERADMIN_PLATAFORMA (cuenta bootstrap)
- Flujo MFA completo: setup → verify → login 2FA → disable
- Password change obligatorio en primer login (must_change_password)
- Refresh token rotation con detección de reuso (token theft)
- Logout revoca solo la sesión actual (sid del token)
- Rate limiting: 2 buckets (login estricto + default) + TRUST_PROXY_HEADERS

#### Roles y Permisos (RBAC)
| Rol | Nivel | MFA Obligatorio | Acceso Admin |
|-----|-------|-----------------|--------------|
| SUPERADMIN_PLATAFORMA | 1 | No (exento, cuenta bootstrap) | Total |
| ADMINISTRADOR_MUNICIPAL | 2 | **Sí** (enforcement server-side) | Municipal |
| GESTOR_LIDER | 3 | No | Gestión equipo |
| GESTOR | 4 | No | Operativo |
| AUDITOR | 4 | No | Solo lectura |
| CONSULTA | 5 | No | Solo lectura |

#### Rutas Protegidas (MFA enforcement)
- `MFA_ALLOWED_SUFFIXES = PASSWORD_CHANGE_ALLOWED_SUFFIXES` (login, change-password, logout, me, refresh, flujo MFA)
- Usuarios con rol en `MFA_ENFORCED_ROLES` (ADMINISTRADOR_MUNICIPAL) sin `mfa_activo` → 403 `MFA_SETUP_REQUIRED` salvo rutas permitidas
- `SUPERADMIN_PLATAFORMA` exento (estado dev documentado sin MFA)

### Usuarios de Prueba
- `admin` / `SigemAdmin2026!` → SUPERADMIN_PLATAFORMA (mfa_activo=f, must_change_password=f)
- `lider01` / `GestorLider2026!` → GESTOR_LIDER
- `enemova` / `EneldoGestor2026!` → GESTOR

### Stack Técnico
- Backend: FastAPI + SQLAlchemy 2.x + PostgreSQL 17 + Redis 7 (Docker puerto 5433/6379)
- Frontend: React 18 + TypeScript + Vite + Tailwind (Docker puerto 3001)
- API: http://localhost:8001/api/v1 (dev) / https://... (prod)
- Frontend: http://localhost:3001 (dev)

### Tests Verificados (Backend)
- ✅ Suite completa: **498 passed, 1 skipped** (0 failed)
- ✅ Gates: ruff, ruff format, mypy (79 archivos), bandit, pytest
- ✅ Cobertura: **59%** (objetivo 80% - gap documentado en decisions.md)
- ✅ Health checks: `/health` (503 si unhealthy), `/health/live`, `/health/ready`, `/metrics` (prometheus-client)
- ✅ JSON logging estructurado, config validation en lifespan

### Tests Verificados (Frontend)
- ✅ **217 tests passed** (13 archivos)
- ✅ Gates: ESLint, tsc --noEmit, npm run test:coverage, npm run build
- ✅ Cobertura global: 18.6% lines / 91.06% branches / 86.02% functions
- ✅ Umbrales per-file ≥80% en componentes críticos (EvidencePreview, EvidenciasModal, UI, api.ts, authStore, LoginPage, ChangePasswordPage)
- ✅ Excepción temporal documentada en `context/decisions.md` con plan de rampa a 80%

### Infraestructura Producción (Fase 1)
- `infra/docker/docker-compose.prod.yml` (postgres/redis/migrate/backend/frontend/nginx/backup + profile monitoring)
- `infra/nginx/nginx.prod.conf` (80→301, TLS 1.2/1.3, HSTS, CSP, rate limits)
- `infra/postgres/init/01-app-role.sh` (rol `sigem_app` + DEFAULT PRIVILEGES, fix B-01)
- `infra/monitoring/prometheus.yml` + `alerts.yml`
- Scripts: `scripts/backup/*` (backup_db/evidencias/retention/run/restore/verify), `scripts/setup/deploy.sh`, `rollback.sh`
- Docs: `docs/operations/{deployment,tls,backups,monitoring,ci-cd}.md`
- Migración 011 corregida (datetime bind para asyncpg)

### CI/CD Pipeline (`.github/workflows/ci.yml`)
- Jobs: backend-quality, backend-tests (postgres+redis services, `--cov-fail-under=80`), frontend-quality, security (gitleaks, pip-audit, npm audit), docker-build, deploy (workflow_dispatch + SSH)
- **Nota:** Gate de cobertura backend (`--cov-fail-under=80`) fallará hasta alcanzar 80% (actual 59%)

### Decisiones Documentadas (`context/decisions.md`)
1. Excepción temporal cobertura frontend + plan de rampa
2. MFA enforcement solo ADMINISTRADOR_MUNICIPAL
3. Logout revoca solo sesión actual
4. Refresh token rotation sin revocación masiva por expiración
5. ValueError → 422 handler para UUID inválidos

### Próximos Pasos para 10/10 Readiness
1. Subir cobertura backend a ≥80% (tests adicionales servicios débiles)
2. Smoke test prod stack (requiere puerto 443 libre en host - HTTP.sys ocupa 443 en Windows)
3. Generar certs self-signed para test local TLS
4. Re-auditoría completa contra checklist
5. Commit + push a GitHub

### Bloqueantes Conocidos
- Puerto 443 ocupado por HTTP.sys (PID 4) en host Windows → nginx prod no puede publicar 443 localmente
- Cobertura backend 59% vs 80% objetivo (requiere ~1080 stmts más)
- Vulnerabilidades npm audit en react-router-dom (transitivas, alpha)