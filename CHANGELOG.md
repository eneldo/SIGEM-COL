# Changelog — SIGEM Colombia

El formato de este archivo se basa en [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] - 2026-09-20

### Added
- Estructura inicial del proyecto según MASTER_PROMPT
- Documentación de auditoría inicial
- Matriz de requisitos completa
- Orden de implementación V1 definido
- Archivos base: README.md, AGENTS.md, PROJECT_RULES.md, ROADMAP.md
- Configuración .gitignore
- Variables de entorno de ejemplo (.env.example)
- Estructura de carpetas completa:
  - agents/
  - context/
  - orchestration/
  - roles/
  - specs/
  - docs/
  - src/
  - tests/
  - migrations/
  - scripts/
  - infra/
  - security/

### Security
- Definición de reglas de seguridad en PROJECT_RULES.md
- Requisitos de MFA documentados
- Requisitos de hashing Argon2id documentados
- Requisitos de RLS documentados

---

## [0.2.0] - 2026-09-20 — Fase 0: Configuración Inicial

### Added
- Backend Python/FastAPI:
  - `pyproject.toml` con dependencias
  - `main.py` con FastAPI app
  - `core/config.py` con settings
  - `core/database.py` con async SQLAlchemy
  - `core/middleware.py` con RequestID y Audit
  - `api/v1/router.py` con router principal
  - `api/v1/auth.py` con endpoints placeholders
  - `api/v1/health.py` con health check
- Frontend React/TypeScript:
  - `package.json` con dependencias
  - `tsconfig.json` y `vite.config.ts`
  - `index.html`, `main.tsx`, `App.tsx`
  - `tailwind.config.js` con paleta SIGEM
  - `src/index.css` con variables CSS
- Infraestructura:
  - `docker-compose.yml` con 5 servicios
  - `Dockerfile` backend y frontend
  - `nginx.conf` con reverse proxy
  - `init.sql` con UUIDv7
- Migraciones:
  - `alembic.ini` y `migrations/env.py`
  - `migrations/script.py.mako`

---

## [0.3.0] - 2026-09-20 — Fase 1: Núcleo Base (Parcial)

### Added
- Modelos de base de datos (18 tablas):
  - `municipios`, `planes_desarrollo`, `vigencias`, `dependencias`
  - `usuarios`, `roles`, `permisos`
  - `usuario_roles`, `rol_permisos`, `usuario_dependencias`
  - `gestores_lideres`, `lineas_estrategicas`, `programas`, `productos`
  - `sesiones`, `intentos_login`, `mfa_factors`, `auditoria_eventos`
- Migraciones Alembic:
  - `001_initial.py` - Esquema completo
  - `002_seed_data.py` - Roles, permisos, municipio default
  - `003_rls_policies.py` - Row-Level Security
- Core de seguridad:
  - `core/security.py` - JWT, Argon2id, tokens
  - `schemas/auth.py` - Pydantic schemas
  - `services/auth_service.py` - Lógica de autenticación
  - `services/audit_service.py` - Logging de eventos
- Endpoints de autenticación:
  - `POST /api/v1/auth/login`
  - `GET /api/v1/auth/me`
  - `POST /api/v1/auth/change-password`
  - `POST /api/v1/auth/logout`

---

## [0.4.0] - 2026-09-20 — Fase 2: Gestores Líderes

### Added
- Schemas Pydantic (`schemas/gestor.py`):
  - GestorCreate, GestorCuenta, GestorPermisos, GestorSeguridad
  - GestorResponse, GestorListResponse, GestorUpdate, GestorFiltros
  - GestorAccion, GestorPasswordReset
- Servicio CRUD (`services/gestor_service.py`):
  - Generación código GES-XXXXXX secuencial
  - Generación username automático (jperez, jperez2...)
  - Contraseña temporal segura (24 caracteres)
  - Crear/.listar/obtener/actualizar gestor
  - Activar/desactivar/bloquear/desbloquear
  - Restablecer contraseña
  - Eliminación lógica
- Endpoints API (`api/v1/gestores.py`):
  - POST /api/v1/gestores
  - GET /api/v1/gestores
  - GET /api/v1/gestores/{id}
  - PUT /api/v1/gestores/{id}
  - POST /api/v1/gestores/{id}/activate
  - POST /api/v1/gestores/{id}/deactivate
  - POST /api/v1/gestores/{id}/block
  - POST /api/v1/gestores/{id}/unblock
  - POST /api/v1/gestores/{id}/reset-password
  - DELETE /api/v1/gestores/{id}
  - GET /api/v1/gestores/{id}/audit

---

## [0.5.0] - 2026-09-20 — Fase 3-5: Líneas, Programas, Productos

### Added
- Schemas Pydantic:
  - `schemas/linea.py` - LineaCreate, LineaUpdate, LineaResponse, LineaListResponse, LineaFiltros
  - `schemas/programa.py` - ProgramaCreate, ProgramaUpdate, ProgramaResponse, ProgramaListResponse, ProgramaFiltros
  - `schemas/producto.py` - ProductoCreate, ProductoUpdate, ProductoResponse, ProductoListResponse, ProductoFiltros
- Servicios CRUD:
  - `services/linea_service.py` - CRUD con validación código único por plan
  - `services/programa_service.py` - CRUD con relación línea
  - `services/producto_service.py` - CRUD con relación programa, dependencia, gestor
- Endpoints API:
  - `api/v1/lineas.py` - 5 endpoints (CRUD completo)
  - `api/v1/programas.py` - 5 endpoints (CRUD completo)
  - `api/v1/productos.py` - 5 endpoints (CRUD completo)

---

## [0.6.0] - 2026-09-20 — Fase 6: Dashboards

### Added
- Servicios de dashboard:
  - `services/dashboard_admin_service.py` - KPIs, resumen plan, gestores, alertas, estadísticas por dependencia
  - `services/dashboard_gestor_service.py` - KPIs personales, mis productos, pendientes, alertas
- Endpoints API:
  - `api/v1/dashboard/admin.py` - 5 endpoints (kpis, resumen-plan, gestores, alertas, estadisticas-dependencia)
  - `api/v1/dashboard/gestor.py` - 4 endpoints (kpis, mis-productos, mis-pendientes, mis-alertas)

---

## [0.7.0] - 2026-09-20 — Frontend React/TypeScript

### Added
- Core:
  - `src/lib/api.ts` - Cliente Axios con interceptores y métodos tipados
  - `src/lib/types.ts` - Tipos TypeScript completos
  - `src/stores/authStore.ts` - Store Zustand con persistencia
- Componentes UI:
  - `components/ui/Button.tsx` - 4 variantes, 3 tamaños, loading
  - `components/ui/Input.tsx` - Label, error, helper text
  - `components/ui/Card.tsx` - Card/Header/Content/Footer
  - `components/ui/Table.tsx` - Genérica con sort, loading, empty
- Layout:
  - `components/layout/Layout.tsx` - Shell con sidebar + header
  - `components/layout/Sidebar.tsx` - Navegación por rol, responsive
  - `components/layout/Header.tsx` - Info usuario, logout
- Páginas auth:
  - `pages/auth/LoginPage.tsx` - Login con municipio, username, password
  - `pages/auth/ChangePasswordPage.tsx` - Cambio obligatorio con strength indicator
- Páginas admin:
  - `pages/admin/DashboardAdmin.tsx` - KPIs + alertas
  - `pages/admin/GestoresPage.tsx` - CRUD completo con filtros y acciones
  - `pages/admin/LineasPage.tsx` - CRUD líneas estratégicas
  - `pages/admin/ProgramasPage.tsx` - CRUD programas
  - `pages/admin/ProductosPage.tsx` - CRUD productos
- Páginas gestor:
  - `pages/gestor/DashboardGestor.tsx` - KPIs personales + productos + pendientes
- Routing:
  - `App.tsx` - Rutas protegidas por rol
  - ProtectedRoute con redirección por mustChangePassword

---

## [Unreleased]

### Pending
- Tests de seguridad (aislamiento, autorización)
- Tests E2E
- MFA WebAuthn
- Notifications system

---

**Nota:** Este changelog será actualizado con cada cambio significativo del proyecto.
