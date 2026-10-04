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
- ✅ Suite completa: **831 passed, 1 skipped** (0 failed)
- ✅ Gates: ruff, ruff format, mypy (79 archivos), bandit, pytest
- ✅ Cobertura de líneas: **100%** (5.011 sentencias, 0 pendientes; gate `--cov-fail-under=100`)
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

### Validación de Continuidad (2026-10-01)
- Cambios frontend pendientes validados: 29 tests focalizados aprobados, ESLint aprobado y build aprobado (`tsc` + Vite).
- El proyecto no define script `npm run typecheck`; el typecheck se ejecuta como parte de `npm run build`.
- `docker compose -f infra/docker/docker-compose.prod.yml config --quiet` aprobado con Docker 28.3.2.
- Preflight productivo: imágenes `sigem-backend`, `sigem-frontend` y `sigem-backup` disponibles; `.env.prod` presente; stack productivo detenido.
- Smoke test TLS completo bloqueado: faltan `infra/tls/cert.pem` y `infra/tls/key.pem`, y el puerto 443 continúa ocupado por HTTP.sys (PID 4). Puerto 80 libre.

### Próximos Pasos para 10/10 Readiness
1. Liberar o remapear el puerto 443 para la validación local.
2. Generar certificados self-signed para el smoke test local TLS.
3. Levantar el stack productivo y ejecutar el checklist post-despliegue.
4. Re-auditoría completa contra checklist.
5. Commit + push a GitHub.

### Bloqueantes Conocidos
- Puerto 443 ocupado por HTTP.sys (PID 4) en host Windows → nginx prod no puede publicar 443 localmente.
- Certificados locales TLS aún no generados.
- Vulnerabilidades npm audit en React Router: 2 moderadas; la corrección automática exige migración disruptiva a React Router 7.

## Continuidad de Producción (2026-10-01)

### Auditoría y correcciones realizadas
- Se ejecutó una auditoría exhaustiva de preparación para producción sobre Docker Compose, Nginx, TLS, CI/CD, backups, rollback, configuración backend y frontend.
- `Settings.validate_production()` ahora rechaza placeholders, secretos débiles o iguales, rol DB distinto de `sigem_app`, Redis sin autenticación, URLs no HTTPS, dominios de ejemplo, CORS inseguro, MFA/rate limiting desactivados y métricas sin token.
- Nginx ahora sobrescribe `X-Forwarded-For` con `$remote_addr` para impedir spoofing de IP desde clientes.
- Cada backup ejecuta `verify_backup.sh` inmediatamente y falla si la verificación no pasa.
- `deploy.sh` y `rollback.sh` validan tags Docker, requieren las tres imágenes inmutables (backend, frontend y backup), usan `--no-build` y ya no construyen código en el servidor.
- `deploy.sh` rechaza placeholders del entorno, certificados inválidos/próximos a expirar y pares certificado/clave que no coincidan; ya no recomienda certificados de desarrollo para producción.
- Se añadieron pruebas para las nuevas validaciones y representaciones de modelos, manteniendo el gate backend al 100%.

### Gates verificados
- Backend: Ruff, Ruff format, mypy y Bandit aprobados.
- Backend: **845 passed, 1 skipped**, 5.078 sentencias, **100% cobertura de líneas**.
- Frontend: TypeScript, ESLint, cobertura y build aprobados.
- Frontend: **443 tests aprobados**, 48,32% líneas / 95,67% branches / 96,18% functions.
- Docker Compose productivo: configuración válida.
- Build frontend: aprobado; advertencia no bloqueante por bundle JS de 572,67 kB.
- `npm audit`: 2 vulnerabilidades moderadas de React Router; la corrección disponible instala React Router 7 y es breaking.

### Decisiones del usuario
- Dominio público: disponible, pero falta recibir el nombre exacto.
- Registro de imágenes: **GitHub Container Registry (GHCR)**.
- Backups externos: **almacenamiento S3 compatible**.

### Datos externos pendientes para completar producción
1. Dominio público exacto y confirmación de DNS apuntando al servidor.
2. Organización/propietario y ruta GHCR (`ghcr.io/<owner>`).
3. Endpoint, región y nombre del bucket S3 compatible.
4. Credenciales de GHCR y S3 configuradas directamente como secretos, nunca compartidas ni guardadas en el repositorio.
5. Certificado TLS confiable para el dominio y puertos públicos 80/443 disponibles.
6. Servidor de producción o staging accesible para levantar el stack, ejecutar migraciones, smoke tests, validación RLS, cabeceras y recuperación de backup.

### Estado de readiness
- Código y gates locales: aprobados.
- Producción real: **aún no aprobada** hasta publicar imágenes inmutables en GHCR, configurar TLS/dominio, habilitar backups S3 cifrados y probar restauración, desplegar en el host objetivo y completar el checklist post-despliegue.

## Auditoría de despliegue Oracle Cloud (2026-10-02)

### Veredicto
- El proyecto todavía no está listo para desplegarse en una VM Oracle Cloud limpia.
- La arquitectura productiva es adecuada: Docker Compose, Nginx TLS, PostgreSQL, Redis, migraciones Alembic, health checks, volúmenes persistentes, límites de recursos, logs rotados y backups locales.
- El despliegue queda condicionado a corregir el empaquetado backend, implementar la distribución de imágenes y completar la preparación del host Oracle.

### Validaciones ejecutadas
- Backend: Ruff, Ruff format, mypy y Bandit aprobados.
- Backend: **845 passed, 1 skipped**, **100% cobertura**.
- Frontend: ESLint, TypeScript, **443 tests**, cobertura y build aprobados.
- Docker Compose productivo: `config --quiet` aprobado.
- Build frontend aprobado con advertencia no bloqueante por bundle JS de 572,67 kB.
- Estado Git durante la auditoría: **11 archivos modificados y 38 archivos sin seguimiento**; no desplegar ni etiquetar hasta revisar y limpiar el árbol de trabajo.

### Bloqueantes técnicos
1. Revisar/corregir `infra/docker/backend/Dockerfile`: actualmente intenta instalar el paquete editable antes de copiar `src/backend`, por lo que un build limpio puede fallar; producción tampoco debe instalar extras `dev`.
2. Implementar entrega de imágenes. `deploy.sh` exige imágenes inmutables, usa `--no-build` y solo intenta descargar nombres locales no cualificados; CI construye backend/frontend sin publicarlos y tampoco construye la imagen de backup.
3. Publicar `sigem-backend`, `sigem-frontend` y `sigem-backup` en GHCR con tags inmutables o digest, y configurar autenticación de la VM.
4. Crear un `.env.prod` exclusivo del servidor con secretos fuertes y únicos, URLs HTTPS reales, CORS restringido y rate limiting/MFA activos. El archivo local de pruebas no debe usarse en Oracle.
5. Instalar certificado TLS confiable y clave coincidente para el dominio real.
6. Corregir Prometheus: `/metrics` exige Bearer token, pero la configuración actual de Prometheus no lo envía. Mantener el perfil de monitoring desactivado hasta resolverlo.
7. Configurar backups externos S3 compatibles y realizar una restauración completa. Los backups actuales permanecen en la misma VM.
8. Documentar/automatizar la rotación de contraseña de `sigem_app`; el script de inicialización PostgreSQL solo se ejecuta con un volumen nuevo.

### Preparación requerida de Oracle Cloud
- VM Linux recomendada para pruebas: mínimo 2 vCPU y 4 GB RAM; preferible 8 GB si se construyen imágenes en el host o se habilita Prometheus.
- Confirmar arquitectura `amd64` o `arm64` y publicar imágenes compatibles.
- Instalar Docker Engine, Docker Compose v2, Git, Bash y OpenSSL; habilitar Docker al iniciar.
- Configurar DNS del dominio hacia la IP pública de la VM.
- OCI NSG/Security List y firewall del sistema: publicar únicamente 80/443; restringir 22 a IPs administrativas; no publicar 5432, 6379, 8000, 3000 ni 9090.
- Dimensionar disco para imágenes, PostgreSQL, Redis, evidencias, logs y retención de backups.
- Mantener PostgreSQL, Redis, backend y frontend únicamente en la red interna de Compose.

### Secuencia acordada de despliegue
1. Corregir Dockerfile backend y pipeline de imágenes GHCR.
2. Revisar y dejar limpio el árbol Git; crear commit/tag inmutable y publicarlo.
3. Preparar VM, DNS, firewall y Docker.
4. Crear `.env.prod` directamente en el servidor sin versionarlo.
5. Instalar certificados en `infra/tls/` y validar vigencia, SAN y correspondencia con la clave.
6. Autenticar Docker contra GHCR y descargar las tres imágenes del mismo tag/digest.
7. Ejecutar `bash scripts/setup/deploy.sh <tag>`.
8. Verificar migración Alembic, estado de contenedores, `/health`, `/health/ready`, frontend, login, MFA, carga/descarga, permisos y aislamiento RLS multi-municipio.
9. Ejecutar y verificar backup, copiarlo fuera del host y completar un ensayo de restauración.
10. Validar cabeceras TLS, logs, reinicio de la VM y procedimiento de rollback.

### Gate para autorizar el servidor de pruebas
- Build limpio de las tres imágenes aprobado.
- Imágenes publicadas y descargables desde GHCR.
- Git limpio y tag inmutable.
- Dominio, DNS, TLS y secretos productivos configurados.
- Migración desde base vacía aprobada y un único head Alembic.
- Aplicación conectada como `sigem_app`, sin superusuario ni `BYPASSRLS`.
- Smoke tests y pruebas de aislamiento aprobados en Oracle.
- Backup externo y restauración comprobados.
- Monitoreo corregido o explícitamente desactivado.
