# Matriz de Requisitos — SIGEM Colombia

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Objetivo:** Mapeo completo de requisitos vs estado de implementación.

---

## Leyenda

- ✅ **Existente** — Requisito implementado y funcional
- ⚠️ **Parcial** — Requisito parcialmente implementado
- ❌ **Faltante** — Requisito no implementado
- 🔴 **Riesgo Alto** — Requisito crítico no implementado
- 🟡 **Riesgo Medio** — Requisito importante no implementado
- 🟢 **Riesgo Bajo** — Requisito deseable no implementado

---

## 1. Arquitectura y Estructura

| # | Requisito | Estado | Riesgo | Archivos Afectados | Notas |
|---|-----------|--------|--------|-------------------|-------|
| 1.1 | Arquitectura modular | ❌ Faltante | 🔴 | `src/` | Solo existe estructura de carpetas |
| 1.2 | Separación de responsabilidades | ❌ Faltante | 🔴 | `src/backend/`, `src/frontend/` | No hay código |
| 1.3 | API-first | ❌ Faltante | 🔴 | `src/backend/` | No hay endpoints definidos |
| 1.4 | Multi-municipio | ❌ Faltante | 🔴 | `src/`, `migrations/` | No hay esquema DB |
| 1.5 | Seguridad por diseño | ❌ Faltante | 🔴 | `security/` | No hay implementación |
| 1.6 | Auditoría por diseño | ❌ Faltante | 🔴 | `src/` | No hay middleware de auditoría |
| 1.7 | Eliminación lógica | ❌ Faltante | 🟡 | `migrations/` | No hay tablas definidas |
| 1.8 | Versionado de evidencias | ❌ Faltante | 🟡 | `src/` | Módulo V1.1 |
| 1.9 | Trazabilidad completa | ❌ Faltante | 🔴 | `src/` | No hay logging estructurado |
| 1.10 | Validación server-side | ❌ Faltante | 🔴 | `src/backend/` | No hay schemas Pydantic |
| 1.11 | Tipado fuerte | ❌ Faltante | 🟡 | `src/` | No hay código TypeScript/Python |
| 1.12 | Pruebas automatizadas | ❌ Faltante | 🔴 | `tests/` | No hay tests |
| 1.13 | Migraciones controladas | ❌ Faltante | 🔴 | `migrations/` | No hay Alembic configurado |
| 1.14 | Documentación viva | ❌ Faltante | 🟡 | `docs/` | Solo existe auditoría inicial |

---

## 2. Stack Tecnológico

| # | Componente | Tecnología | Estado | Riesgo | Notas |
|---|------------|------------|--------|--------|-------|
| 2.1 | Backend | Python 3.12+ | ❌ Faltante | 🔴 | No hay `requirements.txt` o `pyproject.toml` |
| 2.2 | Framework Backend | FastAPI | ❌ Faltante | 🔴 | No hay aplicación FastAPI |
| 2.3 | ORM | SQLAlchemy 2.x | ❌ Faltante | 🔴 | No hay modelos definidos |
| 2.4 | Migraciones | Alembic | ❌ Faltante | 🔴 | No hay configuración Alembic |
| 2.5 | Validación | Pydantic v2 | ❌ Faltante | 🔴 | No hay schemas |
| 2.6 | Base de datos | PostgreSQL 17+ | ❌ Faltante | 🔴 | No hay `docker-compose.yml` |
| 2.7 | Cache | Redis | ❌ Faltante | 🟡 | No hay configuración Redis |
| 2.8 | Frontend | React + TypeScript | ❌ Faltante | 🔴 | No hay `package.json` |
| 2.9 | Build Tool | Vite o Next.js | ❌ Faltante | 🟡 | No hay configuración frontend |
| 2.10 | Contenedores | Docker | ❌ Faltante | 🔴 | No hay Dockerfile |
| 2.11 | Orquestación | Docker Compose | ❌ Faltante | 🔴 | No hay `docker-compose.yml` |
| 2.12 | Reverse Proxy | Nginx | ❌ Faltante | 🟡 | No hay configuración Nginx |
| 2.13 | Hashing Contraseñas | Argon2id | ❌ Faltante | 🔴 | No hay implementación auth |
| 2.14 | MFA | WebAuthn/TOTP | ❌ Faltante | 🔴 | No hay implementación MFA |
| 2.15 | API Documentation | OpenAPI | ❌ Faltante | 🟡 | FastAPI lo genera automáticamente |

---

## 3. Base de Datos

| # | Tabla/Entidad | Estado | Riesgo | Migración Requerida | Notas |
|---|---------------|--------|--------|---------------------|-------|
| 3.1 | `municipios` | ❌ Faltante | 🔴 | Sí | Tabla maestra multi-municipio |
| 3.2 | `planes_desarrollo` | ❌ Faltante | 🔴 | Sí | Planes por municipio |
| 3.3 | `vigencias` | ❌ Faltante | 🔴 | Sí | Años fiscales |
| 3.4 | `dependencias` | ❌ Faltante | 🔴 | Sí | Dependencias municipales |
| 3.5 | `usuarios` | ❌ Faltante | 🔴 | Sí | Usuarios del sistema |
| 3.6 | `gestores_lideres` | ❌ Faltante | 🔴 | Sí | Gestores con permisos |
| 3.7 | `roles` | ❌ Faltante | 🔴 | Sí | Roles del sistema |
| 3.8 | `permisos` | ❌ Faltante | 🔴 | Sí | Permisos granulares |
| 3.9 | `usuario_roles` | ❌ Faltante | 🔴 | Sí | Relación usuario-rol |
| 3.10 | `rol_permisos` | ❌ Faltante | 🔴 | Sí | Relación rol-permiso |
| 3.11 | `usuario_dependencias` | ❌ Faltante | 🔴 | Sí | Relación usuario-dependencia |
| 3.12 | `lineas_estrategicas` | ❌ Faltante | 🔴 | Sí | Líneas del plan |
| 3.13 | `programas` | ❌ Faltante | 🔴 | Sí | Programas por línea |
| 3.14 | `productos` | ❌ Faltante | 🔴 | Sí | Productos por programa |
| 3.15 | `sesiones` | ❌ Faltante | 🔴 | Sí | Control de sesiones |
| 3.16 | `intentos_login` | ❌ Faltante | 🔴 | Sí | Protección login |
| 3.17 | `password_history` | ❌ Faltante | 🟡 | Sí | Historial contraseñas |
| 3.18 | `mfa_factors` | ❌ Faltante | 🔴 | Sí | Factores MFA |
| 3.19 | `auditoria_eventos` | ❌ Faltante | 🔴 | Sí | Log de eventos |
| 3.20 | `auditoria_evidencias` | ❌ Faltante | 🟡 | Sí | Auditoría archivos |
| 3.21 | Row-Level Security | ❌ Faltante | 🔴 | Sí | Políticas RLS |
| 3.22 | Índices optimizados | ❌ Faltante | 🟡 | Sí | Performance |

---

## 4. Seguridad

| # | Requisito | Estado | Riesgo | Implementación Requerida | Notas |
|---|-----------|--------|--------|--------------------------|-------|
| 4.1 | Autenticación JWT | ❌ Faltante | 🔴 | `src/backend/auth/` | Token-based auth |
| 4.2 | RBAC (Role-Based) | ❌ Faltante | 🔴 | `src/backend/security/` | Control por roles |
| 4.3 | ABAC (Attribute-Based) | ❌ Faltante | 🔴 | `src/backend/security/` | Control por atributos |
| 4.4 | PostgreSQL RLS | ❌ Faltante | 🔴 | `migrations/` | Aislamiento a nivel DB |
| 4.5 | MFA Obligatorio Admin | ❌ Faltante | 🔴 | `src/backend/auth/mfa/` | WebAuthn/TOTP |
| 4.6 | Contraseñas Argon2id | ❌ Faltante | 🔴 | `src/backend/auth/` | Hash seguro |
| 4.7 | Rate Limiting | ❌ Faltante | 🔴 | `src/backend/middleware/` | Protección login |
| 4.8 | Login Throttling | ❌ Faltante | 🔴 | `src/backend/auth/` | Bloqueo progresivo |
| 4.9 | Eliminación Lógica | ❌ Faltante | 🟡 | Modelos, queries | Soft delete |
| 4.10 | Control de Sesiones | ❌ Faltante | 🔴 | `src/backend/auth/` | Listar, revocar |
| 4.11 | Auditoría de Acceso | ❌ Faltante | 🔴 | `src/backend/audit/` | IP, user agent, intentos |
| 4.12 | Eventos de Seguridad | ❌ Faltante | 🔴 | `src/backend/audit/` | 16+ eventos tipados |
| 4.13 | Validación MIME/Bytes | ❌ Faltante | 🟡 | `src/backend/storage/` | Prevención malware |
| 4.14 | HTTPS Obligatorio | ❌ Faltante | 🔴 | `infra/nginx/` | Certificados SSL |
| 4.15 | Secretos en Env vars | ❌ Faltante | 🔴 | `.env.example` | Nunca en código |

---

## 5. Backend (API)

| # | Endpoint/Modulo | Estado | Riesgo | Archivos Requeridos | Notas |
|---|-----------------|--------|--------|---------------------|-------|
| 5.1 | `POST /api/v1/auth/login` | ❌ Faltante | 🔴 | `src/backend/api/auth/` | Login |
| 5.2 | `POST /api/v1/auth/logout` | ❌ Faltante | 🔴 | `src/backend/api/auth/` | Logout |
| 5.3 | `POST /api/v1/auth/change-password` | ❌ Faltante | 🔴 | `src/backend/api/auth/` | Cambio contraseña |
| 5.4 | `GET /api/v1/auth/me` | ❌ Faltante | 🔴 | `src/backend/api/auth/` | Usuario actual |
| 5.5 | `POST /api/v1/auth/mfa/*` | ❌ Faltante | 🔴 | `src/backend/api/auth/mfa/` | MFA endpoints |
| 5.6 | `GET /api/v1/gestores` | ❌ Faltante | 🔴 | `src/backend/api/gestores/` | Listar gestores |
| 5.7 | `POST /api/v1/gestores` | ❌ Faltante | 🔴 | `src/backend/api/gestores/` | Crear gestor |
| 5.8 | `PUT /api/v1/gestores/{id}` | ❌ Faltante | 🔴 | `src/backend/api/gestores/` | Editar gestor |
| 5.9 | `DELETE /api/v1/gestores/{id}` | ❌ Faltante | 🔴 | `src/backend/api/gestores/` | Eliminar lógico |
| 5.10 | `GET /api/v1/lineas-estrategicas` | ❌ Faltante | 🔴 | `src/backend/api/lineas/` | CRUD líneas |
| 5.11 | `GET /api/v1/programas` | ❌ Faltante | 🔴 | `src/backend/api/programas/` | CRUD programas |
| 5.12 | `GET /api/v1/productos` | ❌ Faltante | 🔴 | `src/backend/api/productos/` | CRUD productos |
| 5.13 | `GET /api/v1/security/users` | ❌ Faltante | 🔴 | `src/backend/api/security/` | Gestión usuarios |
| 5.14 | `GET /api/v1/security/roles` | ❌ Faltante | 🔴 | `src/backend/api/security/` | Gestión roles |
| 5.15 | `GET /api/v1/security/permissions` | ❌ Faltante | 🔴 | `src/backend/api/security/` | Gestión permisos |
| 5.16 | `GET /api/v1/audit/events` | ❌ Faltante | 🔴 | `src/backend/api/audit/` | Eventos auditoría |
| 5.17 | Formato de Error | ❌ Faltante | 🔴 | `src/backend/core/` | Contrato uniforme |
| 5.18 | Request ID | ❌ Faltante | 🟡 | `src/backend/middleware/` | Trazabilidad |

---

## 6. Frontend

| # | Componente | Estado | Riesgo | Archivos Requeridos | Notas |
|---|------------|--------|--------|---------------------|-------|
| 6.1 | Dashboard Administrador | ❌ Faltante | 🔴 | `src/frontend/pages/admin/` | Vista consolidada |
| 6.2 | Dashboard Gestor | ❌ Faltante | 🔴 | `src/frontend/pages/gestor/` | Vista independiente |
| 6.3 | Login Page | ❌ Faltante | 🔴 | `src/frontend/pages/auth/` | Autenticación |
| 6.4 | Cambio Contraseña | ❌ Faltante | 🔴 | `src/frontend/pages/auth/` | Obligatorio primer login |
| 6.5 | MFA Setup | ❌ Faltante | 🔴 | `src/frontend/pages/auth/` | Configuración MFA |
| 6.6 | Gestores CRUD | ❌ Faltante | 🔴 | `src/frontend/pages/gestores/` | Asistente por pasos |
| 6.7 | Líneas CRUD | ❌ Faltante | 🔴 | `src/frontend/pages/lineas/` | Gestión líneas |
| 6.8 | Programas CRUD | ❌ Faltante | 🔴 | `src/frontend/pages/programas/` | Gestión programas |
| 6.9 | Productos CRUD | ❌ Faltante | 🔴 | `src/frontend/pages/productos/` | Gestión productos |
| 6.10 | Seguridad/Usuarios | ❌ Faltante | 🔴 | `src/frontend/pages/security/` | Admin usuarios |
| 6.11 | Auditoría | ❌ Faltante | 🟡 | `src/frontend/pages/audit/` | Log eventos |
| 6.12 | Componentes Reutilizables | ❌ Faltante | 🟡 | `src/frontend/components/` | UI library |
| 6.13 | Rutas Protegidas | ❌ Faltante | 🔴 | `src/frontend/router/` | Guard auth |
| 6.14 | Control de Sesión | ❌ Faltante | 🔴 | `src/frontend/context/` | Estado auth |
| 6.15 | Diseño Responsive | ❌ Faltante | 🟡 | Estilos | Mobile-first |
| 6.16 | Accesibilidad WCAG 2.2 AA | ❌ Faltante | 🟡 | Componentes | Labels, ARIA |

---

## 7. Infraestructura

| # | Componente | Estado | Riesgo | Archivos Requeridos | Notas |
|---|------------|--------|--------|---------------------|-------|
| 7.1 | Dockerfile Backend | ❌ Faltante | 🔴 | `infra/docker/backend/` | Imagen Python |
| 7.2 | Dockerfile Frontend | ❌ Faltante | 🔴 | `infra/docker/frontend/` | Imagen Node |
| 7.3 | docker-compose.yml | ❌ Faltante | 🔴 | `infra/docker/` | Orquestación servicios |
| 7.4 | Nginx Config | ❌ Faltante | 🟡 | `infra/nginx/` | Reverse proxy |
| 7.5 | PostgreSQL Init | ❌ Faltante | 🔴 | `infra/postgres/` | Scripts init |
| 7.6 | Redis Config | ❌ Faltante | 🟡 | `infra/redis/` | Cache config |
| 7.7 | .env.example | ❌ Faltante | 🔴 | raíz | Variables entorno |
| 7.8 | .gitignore | ❌ Faltante | 🟡 | raíz | Archivos ignorados |
| 7.9 | HTTPS/SSL | ❌ Faltante | 🔴 | `infra/nginx/` | Certificados |
| 7.10 | Backups | ❌ Faltante | 🟡 | `scripts/backup/` | Automatización |
| 7.11 | Health Checks | ❌ Faltante | 🟡 | `infra/docker/` | Monitoreo |

---

## 8. Pruebas

| # | Tipo de Prueba | Estado | Riesgo | Directorio | Notas |
|---|----------------|--------|--------|------------|-------|
| 8.1 | Unit Tests Backend | ❌ Faltante | 🔴 | `tests/backend/` | Pytest |
| 8.2 | Unit Tests Frontend | ❌ Faltante | 🔴 | `tests/frontend/` | Jest/Vitest |
| 8.3 | Integration Tests | ❌ Faltante | 🔴 | `tests/integration/` | API + DB |
| 8.4 | Authorization Tests | ❌ Faltante | 🔴 | `tests/security/` | RBAC/ABAC |
| 8.5 | RLS Tests | ❌ Faltante | 🔴 | `tests/security/` | Aislamiento |
| 8.6 | Validation Tests | ❌ Faltante | 🟡 | `tests/backend/` | Pydantic |
| 8.7 | Security Tests | ❌ Faltante | 🔴 | `tests/security/` | Vulnerabilidades |
| 8.8 | E2E Tests | ❌ Faltante | 🔴 | `tests/e2e/` | Playwright/Cypress |
| 8.9 | Isolation Tests | ❌ Faltante | 🔴 | `tests/security/` | Multi-municipio |
| 8.10 | Load Tests | ❌ Faltante | 🟡 | `tests/` | Performance |

---

## 9. Documentación

| # | Documento | Estado | Riesgo | Ubicación | Notas |
|---|-----------|--------|--------|-----------|-------|
| 9.1 | README.md | ❌ Faltante | 🟡 | raíz | Guía inicio |
| 9.2 | AGENTS.md | ❌ Faltante | 🟡 | raíz | Agentes IA |
| 9.3 | PROJECT_RULES.md | ❌ Faltante | 🟡 | raíz | Reglas |
| 9.4 | ROADMAP.md | ❌ Faltante | 🟡 | raíz | Hoja de ruta |
| 9.5 | CHANGELOG.md | ❌ Faltante | 🟡 | raíz | Historial |
| 9.6 | API Docs | ❌ Faltante | 🟡 | `docs/api/` | OpenAPI auto |
| 9.7 | Architecture Docs | ⚠️ Parcial | 🟡 | `docs/architecture/` | Solo auditoría |
| 9.8 | Security Docs | ❌ Faltante | 🟡 | `docs/security/` | Políticas |
| 9.9 | Database Docs | ❌ Faltante | 🟡 | `docs/database/` | ERD, esquemas |
| 9.10 | User Guides | ❌ Faltante | 🟢 | `docs/user_guides/` | Manuales |

---

## 10. Resumen de Cobertura

| Categoría | Total Requisitos | Existente | Parcial | Faltante | Cobertura |
|-----------|------------------|-----------|---------|----------|-----------|
| Arquitectura | 14 | 0 | 0 | 14 | 0% |
| Stack | 15 | 0 | 0 | 15 | 0% |
| Base de Datos | 22 | 0 | 0 | 22 | 0% |
| Seguridad | 15 | 0 | 0 | 15 | 0% |
| Backend API | 18 | 0 | 0 | 18 | 0% |
| Frontend | 16 | 0 | 0 | 16 | 0% |
| Infraestructura | 11 | 0 | 0 | 11 | 0% |
| Pruebas | 10 | 0 | 0 | 10 | 0% |
| Documentación | 10 | 0 | 1 | 9 | 5% |
| **TOTAL** | **131** | **0** | **1** | **130** | **0.76%** |

---

## 11. Conclusión

El proyecto se encuentra en **fase de especificación pura**. No existe código funcional. La cobertura total es del **0.76%** (solo existe la estructura de carpetas y un documento de auditoría).

**Próxima acción requerida:**  
Iniciar **Fase 1 — Núcleo Base** según el orden definido en el MASTER_PROMPT.

---

**Documento generado como parte de la auditoría inicial — Sección 62 del MASTER_PROMPT**
