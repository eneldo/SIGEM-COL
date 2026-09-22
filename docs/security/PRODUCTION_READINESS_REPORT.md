# SIGEM Colombia — Production Readiness Report

**Fecha:** 2026-09-22  
**Estado:** ❌ NO LISTO PARA PRODUCCIÓN  
**Hallazgos CRÍTICOS:** 7 | **ALTOS:** 11 | **MEDIOS:** 14 | **BAJOS:** 9

---

## Resumen Ejecutivo

El sistema tiene una buena arquitectura base y código limpio, pero contiene **7 vulnerabilidades críticas** que impiden un despliegue seguro en producción. Los problemas más graves son: RLS inactivo (aislamiento multi-municipio comprometido), secretos hardcodeados en Docker, sin HTTPS, contenedor como root, y RBAC placeholder en dashboards.

**Lo que SÍ funciona bien:**
- ✅ SQL Injection: LIMPIO — todas las queries usan SQLAlchemy ORM parametrizado
- ✅ Password hashing: Argon2id con configuración OWASP-compliant
- ✅ JWT: HS256 con expiración 15min, secretos de 64 bytes
- ✅ Autenticación: Todos los endpoints (excepto health) requieren token
- ✅ Security headers: X-Frame-Options, X-Content-Type-Options, HSTS
- ✅ CORS: Configurado con orígenes explícitos (no wildcard)
- ✅ TypeScript: Strict mode habilitado
- ✅ Auditoría: Middleware de logging sin datos sensibles

---

## HALLAZGOS CRÍTICOS (Bloquean Producción)

### CRIT-01: Row-Level Security (RLS) INACTIVO
**Archivos:** `migrations/versions/003_rls_policies.py`, `src/backend/core/database.py`  
**Impacto:** El aislamiento multi-municipio está comprometido. Cualquier usuario autenticado podría potencialmente acceder a datos de otros municipios.

Las políticas RLS están creadas en PostgreSQL pero la función `set_current_municipio()` **nunca se ejecuta** en la sesión de base de datos. Las políticas evalúan como permisivas.

**Corrección:** En `database.py:get_db()`, antes de yield:
```python
await session.execute(
    text("SELECT set_config('app.current_municipio_id', :mid, true)"),
    {"mid": str(municipio_id)}
)
```

### CRIT-02: Contenedor Backend ejecuta como root
**Archivo:** `infra/docker/backend/Dockerfile`  
**Impacto:** Si un atacante escapa de la aplicación, tiene acceso root al contenedor.

**Corrección:** Agregar `RUN addgroup --system app && adduser --system --ingroup app app` y `USER app`.

### CRIT-03: Secretos hardcodeados en docker-compose
**Archivo:** `infra/docker/docker-compose.yml` (líneas 16, 56-59)  
**Impacto:** Credenciales de PostgreSQL en texto plano. Puerto 5432 expuesto a la red del host.

**Corrección:** Usar `env_file:` en vez de valores hardcodeados. Eliminar `ports: 5432:5432`.

### CRIT-04: Sin HTTPS/TLS
**Archivo:** `infra/nginx/nginx.conf`  
**Impacto:** Tokens JWT, contraseñas y datos viajan en texto plano.

**Corrección:** Configurar TLS con certificados Let's Encrypt o proxy inverso con TLS.

### CRIT-05: RBAC placeholder en dashboards
**Archivos:** `dashboard/admin.py` (líneas 34-57), `dashboard/gestor.py` (líneas 36-59)  
**Impacto:** Cualquier usuario autenticado puede acceder a todos los dashboards admin y gestor sin verificación de permisos.

**Corrección:** Reemplazar `_require_permission()` stub con `await require_permission(db, user_id, perm)`.

### CRIT-06: Puerto PostgreSQL expuesto
**Archivo:** `infra/docker/docker-compose.yml` (líneas 54-55)  
**Impacto:** Base de datos accesible desde la red del host con credenciales conocidas.

**Corrección:** Eliminar el mapeo de puertos. Usar solo red interna de Docker.

### CRIT-07: Puerto Redis expuesto sin autenticación
**Archivo:** `infra/docker/docker-compose.yml` (líneas 76-77)  
**Impacto:** Datos en caché (incluyendo tokens de sesión) accesibles sin autenticación.

**Corrección:** Agregar `--requirepass` al comando Redis y eliminar exposición de puerto.

---

## HALLAZGOS ALTOS

| # | Hallazgo | Archivo | Corrección |
|---|----------|---------|------------|
| HIGH-01 | `--reload` en Dockerfile CMD (producción) | `Dockerfile:28` | Eliminar `--reload` |
| HIGH-02 | Adminer expuesto sin autenticación | `docker-compose.yml:89-102` | Eliminar o agregar auth |
| HIGH-03 | CSP permite `unsafe-inline` y `unsafe-eval` | `nginx.conf:12` | Usar nonces/hashes |
| HIGH-04 | RBAC faltante en dependencias | `dependencias.py` | Agregar `require_permission()` |
| HIGH-05 | MFA deshabilitado en .env | `.env:23` | Habilitar `MFA_ENABLED=true` |
| HIGH-06 | Password schema min_length=8 vs política=15 | `configuracion.py:17` | Aumentar a 15 |
| HIGH-07 | DB password hardcodeada en alembic.ini | `alembic.ini:41` | Leer de env var |
| HIGH-08 | Tabla `avance_producto` sin RLS | `003_rls_policies.py` | Crear migración RLS |
| HIGH-09 | Logging no configurado (LOG_LEVEL/LOG_FORMAT ignorados) | `config.py:72-73` | Configurar Python logging |
| HIGH-10 | Documentación de seguridad vacía | `security/` directories | Crear políticas |
| HIGH-11 | Volume mount + reload = superficie de RCE | `Dockerfile + docker-compose` | Eliminar en producción |

---

## HALLAZGOS MEDIOS

| # | Hallazgo | Corrección |
|---|----------|------------|
| MED-01 | Rate limiter solo per-IP, in-memory | Migrar a Redis + per-user en login |
| MED-02 | CORS solo localhost | Configurar dominio production |
| MED-03 | DEBUG=true por defecto | Forzar DEBUG=false en producción |
| MED-04 | DB echo logging en DEBUG | Verificar production .env |
| MED-05 | JWT secrets auto-generados (no persistentes) | Fijar en env vars de producción |
| MED-06 | RBAC faltante en reportes | Agregar permisos |
| MED-07 | RBAC faltante en cumplimiento | Agregar permisos |
| MED-08 | RBAC faltante en gestor_dashboard | Agregar permisos |
| MED-09 | ValueError mensajes filtran info interna | Generic messages |
| MED-10 | max_length faltante en Update schemas | Agregar constraints |
| MED-11 | Sin Permissions-Policy header | Agregar en nginx |
| MED-12 | Sin rate limiting en nginx | Agregar limit_req |
| MED-13 | Sin client_max_body_size en nginx | Agregar limit |
| MED-14 | Health check no verifica Redis | Agregar check Redis |

---

## HALLAZGOS BAJOS

| # | Hallazgo |
|---|----------|
| LOW-01 | .env.example usa passwords reales |
| LOW-02 | HS256 aceptable, RS256 más seguro |
| LOW-03 | Sin endpoint /refresh token |
| LOW-04 | Admin roles bypass total RBAC |
| LOW-05 | Sin PII redaction framework |
| LOW-06 | Sin SSL en DB connection string |
| LOW-07 | tsconfig skipLibCheck=true |
| LOW-08 | Dependencias no version-pinned |
| LOW-09 | Health check redundante (shallow + deep) |

---

## LO QUE SÍ ESTÁ LISTO

| Componente | Estado | Detalle |
|------------|--------|---------|
| SQL Injection | ✅ LIMPIO | SQLAlchemy ORM parametrizado en todo |
| Password Hashing | ✅ EXCELENTE | Argon2id, OWASP-compliant |
| JWT | ✅ BUENO | HS256, 15min expiry, 64-byte secrets |
| Autenticación | ✅ BUENO | Todos los endpoints protegidos |
| Security Headers | ✅ BUENO | X-Frame, X-Content-Type, HSTS, XSS-Protection |
| CORS | ✅ BUENO | Orígenes explícitos, credentials=True |
| TypeScript | ✅ BUENO | Strict mode + noUnusedLocals |
| Auditoría | ✅ BUENO | Middleware sin datos sensibles |
| Health Check | ✅ BUENO | Deep check con SELECT 1 |

---

## PLAN DE CORRECCIÓN PRIORITARIO

### Fase 1 — INMEDIATO (antes de cualquier despliegue)
1. Activar RLS en database.py (CRIT-01)
2. Eliminar secretos hardcodeados de docker-compose (CRIT-03, CRIT-06, CRIT-07)
3. Contenedor como non-root (CRIT-02)
4. Reemplazar RBAC placeholder en dashboards (CRIT-05)
5. Configurar HTTPS en nginx (CRIT-04)

### Fase 2 — ALTA (antes de producción)
6. RBAC en dependencias, reportes, cumplimiento (HIGH-04, MED-06, MED-07)
7. MFA habilitado (HIGH-05)
8. Password policy enforced (HIGH-06)
9. Rate limiting per-user en login (MED-01)
10. Logging configurado (HIGH-09)

### Fase 3 — MEDIA (post-despliegue)
11. Rate limiting en nginx (MED-12)
12. CSP sin unsafe-inline (HIGH-03)
13. Health check Redis (MED-14)
14. Actualizar CORS para dominio production (MED-02)
15. Eliminar --reload del Dockerfile (HIGH-01)

---

## VEREDICTO FINAL

**¿Está listo para producción?** ❌ NO

**Razón:** 7 vulnerabilidades críticas requieren corrección inmediata. El más grave es el RLS inactivo que compromete el aislamiento multi-municipio (requerimiento fundamental del sistema). Una vez corregidos los hallazgos críticos y altos, el sistema estará en condiciones seguras para despliegue.
