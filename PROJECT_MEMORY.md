# SIGEM Colombia - Project Memory

## Estado Actual (2026-10-21) - Auditoría integral completada y remediación aplicada

### Estado de despliegue
**NO LISTO todavía.** Tres fases de auditoría cierre de código están hechas y verificadas:
(1) RLS/multi-municipio (fase 1), (2) auditoría de plataforma + login multi-municipio (fase 2),
(3) auditoría integral del repositorio con remediación frontend/infra/CI/monitoring/backups (fase 3).
Quedan abiertas solo las deudas documentadas (abajo) y acciones operativas fuera del repositorio
(rotación de credenciales ya no versionadas, aplicar migración 022, activar `sigem_app`).
El flujo de MFA en el frontend sigue siendo **bloqueante de despliegue** (B-1).

### Commits Recientes (pendientes de push)
- **Todo** el trabajo de las tres fases está **sin commitear** en el working tree (~57 archivos
  modificados/borrados/nuevos). Propuesta pendiente: ~6 commits temáticos
  (RLS core / auditoría plataforma / login / infra / CI+gitleaks / frontend).
- `src/backend/uv.lock` es **nuevo y sin trackear** y `infra/docker/backend/Dockerfile` lo copia:
  sin `git add` del lockfile, el build de imagen falla desde un checkout limpio.
- Migración `022_auditoria_plataforma` es el nuevo head (verificada con `alembic history`,
  NO ejecutada).

### Resumen de remediación aplicada (2026-10-21, con referencias)

**Backend RLS (fase 1):** `core/database.py` (`release_tenant_context`, `assert_restricted_db_role`,
`get_db_with_rls = get_db` sesión única), guardia en `main.py` lifespan, validación cross-tenant de
`dependencia_id` en `services/usuario_service.py`, `scripts/setup/bootstrap_admin.py` libera contexto,
scripts `check_*.py` de `scripts/setup` eliminados, tests de aislamiento con guardia de revisión.

**Backend (fase 2):** `models/auditoria_plataforma.py` + `AuditService.log_platform_event` (append-only:
`REVOKE ALL` + `GRANT INSERT` para `sigem_app` idempotente), `authenticate_user` resuelve municipio
por `municipio_codigo` opcional del `LoginRequest` (422 `MUNICIPIO_REQUERIDO` si hay varios activos),
`KNOWN_REVISIONS` incluye `022_auditoria_plataforma`.

**Auditoría integral (fase 3), cambios:**
- Frontend: guardas `requiredRole` (`App.tsx` `/admin`→admins, `/gestor`→admin+gestoress) con fuente
  única `src/lib/roles.ts`; dead-deps fuera del tree (`react-hook-form`, `@hookform/resolvers`,
  `zod`, `date-fns`, `react-router`); alias `@` corregido (vite.config.ts + tsconfig.json)
  — **el alias YA FUNCIONA**, la nota antigua de "usar imports relativos" está obsoleta;
  `EvidencePreview.test.ts` duplicado eliminado; CSP meta en `index.html`.
- Nginx prod: `nginx.prod.conf` es plantilla (montada en `/etc/nginx/templates/nginx.conf.template`,
  `NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx`), vhost `default_server` con `return 444` y
  `ssl_reject_handshake on`; `server_name ${SIGEM_DOMAIN}`; local idéntico con `localhost 127.0.0.1`.
- `deploy.sh`: valida `SIGEM_DOMAIN` ⊇ host de `FRONTEND_URL` (falla rápido si no).
- Backups: cifrado at-rest opcional `BACKUP_ENCRYPTION_PASSPHRASE` (AES-256-CBC+PBKDF2/200k,
  passphrase solo por env, plaintext eliminado salvo `BACKUP_KEEP_PLAINTEXT=true`);
  `BACKUP_REQUIRE_OFFSITE=true` falla sin `BACKUP_RSYNC_TARGET`; `restore_db.sh` descifra a temporal;
  `verify_backup.sh` salta `pg_restore --list` en `*.dump.enc`.
- Monitoring: `prometheus.yml` con `bearer_token_file` (token escrito en entrypoint del contenedor
  desde `METRICS_TOKEN`) y bloque `alerting:`→`alertmanager:9093`; servicio `alertmanager` nuevo
  (perfil monitoring local/prod, `127.0.0.1:9093`); 2 alertas muertas retiradas
  (`pg_stat_activity_count`, `node_filesystem_*` — sin exporters); `infra/monitoring/alertmanager.yml`
  con SMTP placeholders a sustituir antes de prod.
- CI: `permissions: contents: read` top-level; `deploy` con `environment: production` + 
  `concurrency: deploy-production` + `needs` incluye `docker-build`; `.gitleaks.toml` con allowlist
  por commit del hallazgo histórico (`abde3f3b…`, credencial de test ya ausente en HEAD) → gitleaks limpio.
- Composes: puertos de gestión en `127.0.0.1` (dev 5433/8001/3001, local 8080/8443); `version: '3.8'`
  obsoleto retirado del compose local; los 3 compose validados con `docker compose config`.
- Higiene raíz: `check_*.py`/`test_*`/`test_login.json` (con credenciales en claro, nunca trackeados)
  eliminados del disco; `current-page.yml` borrado del índice; `privkey.pem`/`fullchain.pem` en 600
  y `generate_dev_cert.sh` verifica el modo en runtime.
- Ping de notificación automático en ambos composes con los servicios Prometheus/Alertmanager.

**Pendientes operativos fuera del repositorio** (bloqueados por credenciales de BD del host):
1. Aplicar `alembic upgrade head` (→ `022_auditoria_plataforma`).
2. Crear `sigem_app` LOGIN y conmutar `.env` (`DATABASE_URL` → rol restringido; bloque SQL entregado
   en sesión y script idempotente `scripts/setup/grant_app_role_local.py`).
3. Con BD activa: correr `pytest tests/security/test_rls_isolation.py` (8 tests deben dejar de skip).
4. Rotar la credencial de BD que quedó en los scripts `check_*` borrados (si salió del entorno controlado).
5. **B-1 (bloqueante): implantar el flujo MFA en el SPA.**

### Estado de Funcionalidades

#### Autenticación y Autorización
- Login: usuario + contraseña (+ `municipio_codigo` opcional; se resuelve el único municipio activo o se exige selección `MUNICIPIO_REQUERIDO` — `00000` en duro eliminado)
- **Tabla `auditoria_plataforma`** (migración `022`, pendiente de aplicar en la BD local): eventos sin municipio, append-only para `sigem_app`
- **Frontend:** guardas de ruta (`requiredRole`) en `/admin/*` y `/gestor/*`; roles centralizados en `src/lib/roles.ts`; CSP en `index.html`; dependencias muertas eliminadas
- **Infra:** `SIGEM_DOMAIN` requerido en prod (nginx plantilla + descarte de Host/SNI); `deploy.sh` valida dominio↔FRONTEND_URL; backups cifrables y off-site exigible; Prometheus con token + Alertmanager; puertos de gestión en loopback; CI con `permissions` mínimos y deploy con `environment: production`; gitleaks con allowlist de commit histórico (misma credencial de test eliminada en HEAD)

#### Deudas documentadas (auditoría 2026-10-21, aplazadas con justificación en context/decisions.md)
- `reportes.py`/`cumplimiento.py` authentication-only por diseño (si un municipio lo quiere restringir: permiso `REPORTES_VER` con seed + roles + coordinación SPA)
- Umbrales de cobertura global del frontend en 17%: cobertura global real 50% (páginas gestor con 0 tests, ~3.600 líneas) — subir threshold requiere tests primero
- Archivos frontend >500 líneas (GestorEquipoPage 802, RegistroAvancePage 698, types.ts 590…) sin dividir
- E2E Playwright: `tests/e2e/` y `tests/frontend/` vacíos; instalar requiere red
- `set_real_ip_from`/`real_ip_header` en nginx prod: pendiente de topología real (CDN/LB)
- `SIGEM_BOOTSTRAP_PASSWORD` literal en ci.yml aceptado (debe coincidir con `ADMIN_PASSWORD` de tests/conftest.py; job efímero)
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

### Tests Verificados (Backend, estado 2026-10-21)
- ✅ Suite completa: **525 passed, 8 skipped, 0 failed** + 475 ERROR preexistentes por
  `InvalidPasswordError` (credenciales de BD del host desconocidas; NO es código nuevo).
  El enlace de los 475 errores es ambiental: la BD vive en PostgreSQL 18.6 (127.0.0.1:5432) y
  las credenciales del `.env` (`sigem`/`sigem_app`) fallan; el socket de Docker es inaccesible
  por permisos (sudo no disponible).
- ✅ Cobertura de líneas: **100 %** en módulos tocados (gate local `--cov-fail-under=100`)
- ✅ Gates: ruff, ruff format, mypy (87 archivos), bandit `-ll` (0 medio/alto)
- ✅ Migraciones: cadena lineal 001→`022_auditoria_plataforma`, head único, verificada
  con `alembic history` (NO ejecutadas contra BD)

### Tests Verificados (Frontend, estado 2026-10-21)
- ✅ **477 tests passed** (31 archivos; −3 por eliminación del `.test.ts` duplicado)
- ✅ Gates: ESLint (0 warnings), tsc + vite build, vitest
- Cobertura global real **50%** (páginas gestor sin tests ~3.600 líneas); threshold global
  dejó en 17 intencionalmente — ver deudas documentadas
- Excepción temporal de cobertura global documentada en `context/decisions.md` (páginas de dominio
  aún sin tests)

### Seguridad de Datos (RLS)
- RLS habilitado y forzado (`FORCE ROW LEVEL SECURITY`) desde la revisión `017_enforce_rls`
- Rol runtime `sigem_app`: sin SUPERUSER, sin BYPASSRLS, sin CREATE sobre el esquema, solo DML
- **Higiene de pool (2026-10-21)**: cada conexión se devuelve al pool con `RESET app.current_municipio_id` (`release_tenant_context`); `get_db_with_rls` es ahora alias de `get_db` (una sola sesión por request)
- **Guardia de arranque (2026-10-21)**: `assert_restricted_db_role()` CRÍTICA en dev (el `.env` local conecta como `sigem`, SUPERUSER = RLS sin efecto) y fail-fast en producción
- **Validación cross-tenant (2026-10-21)**: `dependencia_id` de `create_usuario` se valida bajo el tenant antes de la asociación
- **Pendiente operativo**: activar `sigem_app` (LOGIN/contraseña + grants con `scripts/setup/grant_app_role_local.py`) sobre la BD restaurada del host y conmutar `.env`; **rotar la credencial filtrada** (verificada presente en scripts `check_*.py` ya eliminados del working tree; historial git no trackeó los archivos)
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
