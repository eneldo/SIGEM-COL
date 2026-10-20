# SIGEM Colombia - Project Memory

## Estado Actual (2026-10-06) - Hardening de seguridad previo a producción

### Estado de despliegue
**NO LISTO todavía.** La auditoría de bloqueantes está cerrada en el código, pero quedan dos
puntos abiertos documentados en `.opencode/memory.md` (flujo de MFA en el frontend y gate de
gitleaks sobre el historial) y acciones operativas fuera del repositorio (rotar y purgar la
credencia que estuvo versionada).

### Commits Recientes (pendientes de push)
- Todo el hardening de seguridad de esta sesión está **sin commitear** en el working tree.
- `src/backend/uv.lock` es **nuevo y sin trackear** y `infra/docker/backend/Dockerfile` lo copia:
  sin `git add` del lockfile, el build de imagen falla desde un checkout limpio.

### Estado de Funcionalidades

#### Autenticación y Autorización
- Login: usuario + contraseña + municipio
- **MFA TOTP obligatorio para ADMINISTRADOR_MUNICIPAL y SUPERADMIN_PLATAFORMA**
  (`MFA_ENFORCED_ROLES` en `src/backend/api/v1/auth.py:56`)
- Flujo MFA de backend completo: setup → verify → login 2FA → disable
- **Pendiente: la SPA no implementa el flujo MFA** (ni setup ni challenge) → bloqueante de despliegue
- Secretos TOTP cifrados en reposo con `ENCRYPTION_KEY` (AES-GCM, formato `enc:v1:`)
- Password change obligatorio en primer login (must_change_password)
- Refresh token en **cookie HttpOnly** (`SameSite=Strict`, `Path=/api/v1/auth`), con validación de
  `Origin`; access token solo en memoria en el navegador
- Logout revoca solo la sesión actual (sid del token) y borra la cookie
- Rate limiting **distribuido con Redis**: 2 ventanas (general y login) y fail-closed en el bucket
  de autenticación
- JWT con `TokenClaims` tipado: claims inválidos → 401, nunca 500

#### Roles y Permisos (RBAC)
| Rol | Nivel | MFA Obligatorio | Acceso Admin |
|-----|-------|-----------------|--------------|
| SUPERADMIN_PLATAFORMA | 1 | **Sí** | Total |
| ADMINISTRADOR_MUNICIPAL | 2 | **Sí** | Municipal |
| GESTOR_LIDER | 3 | No | Gestión equipo |
| GESTOR | 4 | No | Operativo |
| AUDITOR | 4 | No | Solo lectura |
| CONSULTA | 5 | No | Solo lectura |

#### Rutas Protegidas (MFA enforcement)
- `MFA_ALLOWED_SUFFIXES = PASSWORD_CHANGE_ALLOWED_SUFFIXES` (login, change-password, logout, me, refresh, flujo MFA)
- Usuarios con rol en `MFA_ENFORCED_ROLES` sin `mfa_activo` → 403 `MFA_SETUP_REQUIRED` salvo rutas permitidas

### Usuarios de Prueba
- Las credenciales no se versionan. Los tests que requieren una cuenta administrativa reciben
  `SIGEM_TEST_ADMIN_PASSWORD` desde el entorno y crean usuarios aislados mediante fixtures.

### Stack Técnico
- Backend: FastAPI + SQLAlchemy 2.x + PostgreSQL 17 + Redis 7 (Docker puerto 5433/6379)
- **JWT: PyJWT** (se sustituyó `python-jose`, que tenía `GHSA-3qf3-8w2g-rqmx` y arrastraba `ecdsa`)
- Frontend: React 18 + TypeScript + Vite + Tailwind (Docker puerto 3001)
- API: http://localhost:8001/api/v1 (dev) / https://... (prod)
- Frontend: http://localhost:3001 (dev)

### Tests Verificados (Backend)
- ✅ Suite completa: **575 passed, 387 skipped** (los skipped requieren `SIGEM_TEST_ADMIN_PASSWORD`)
- ✅ Cobertura de líneas: **100 %** (5.349 sentencias, 0 pendientes; gate `--cov-fail-under=100`)
- ✅ Gates: ruff, ruff format, mypy (86 archivos), bandit (0 medio/alto)
- ✅ `pip_audit --strict` sobre el conjunto bloqueado de producción: **0 vulnerabilidades**
- ✅ Migraciones: cadena lineal 001→020, head único, aplicadas desde cero sobre base limpia

### Tests Verificados (Frontend)
- ✅ **480 tests passed** (32 archivos)
- ✅ Gates: ESLint (0 warnings), tsc --noEmit, vitest, build
- ✅ `npm audit --omit=dev`: **0 vulnerabilidades**
- Excepción temporal de cobertura global documentada en `context/decisions.md` (páginas de dominio
  aún sin tests)

### Seguridad de Datos (RLS)
- RLS habilitado y forzado (`FORCE ROW LEVEL SECURITY`) desde la revisión `017_enforce_rls`
- Rol runtime `sigem_app`: sin SUPERUSER, sin BYPASSRLS, sin CREATE sobre el esquema, solo DML
- **Advertencia**: el rol de migración `sigem` es superusuario y **ignora RLS**; las pruebas de
  aislamiento deben ejecutarse con un rol restringido (`tests/security/test_rls_isolation.py`)

### Documentación Actualizada
- `docs/security/PRODUCTION_READINESS_REPORT.md`: cabecera con el cierre de la auditoría y tabla
  hallazgo → corrección → evidencia
- `docs/operations/deployment.md`: checklist con cookie de sesión y verificación de RLS
- `docs/operations/ci-cd.md`: pip-audit sin CVEs ignorados, npm audit sin excepciones
- `context/decisions.md`: 5 decisiones nuevas (MFA superadmin, cookie de refresco, rate limiting
  distribuido, validación RLS con rol restringido, cifrado TOTP)
- `CHANGELOG.md`: cambios de la sesión en Added/Changed/Security
