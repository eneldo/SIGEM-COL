# SIGEM Colombia - Project Memory

## Estado Actual (2026-09-30)

### Commits Recientes
1. **ad9fc8d** - fix: allow both SUPERADMIN_PLATAFORMA and ADMINISTRADOR_MUNICIPAL for gestor config routes
2. **9aad469** - fix: remove Dependencias and Configuracion from Gestor Lider portal
3. **d3ed923** - feat: simplify login - remove MFA enforcement and municipio field
4. **4e6347e** - fix: auditoría completa — 8 hallazgos críticos resueltos

### Estado de Funcionalidades

#### Autenticación (Simplificada)
- Login: solo usuario + contraseña (sin municipio, sin MFA)
- Usuario admin: `admin` / `SigemAdmin2026!`
- Usuario coordinador: `lider01` / `GestorLider2026!`

#### Roles y Permisos
| Rol | Menu Items | /gestor/configuracion | /gestor/configuracion/dependencias |
|-----|------------|----------------------|-----------------------------------|
| **Coordinador (GESTOR_LIDER)** | 7 (Dashboard, Equipo, Asignar, Mis Avances, Revisión, Cumplimiento, Reportes) | ❌ Bloqueado | ❌ Bloqueado |
| **Admin (SUPERADMIN_PLATAFORMA)** | 10 (incluye Dependencias, Configuración) | ✅ Permitido | ✅ Permitido |

#### Rutas Protegidas (App.tsx)
- `/gestor/configuracion` → `ProtectedRoute requiredRole={['SUPERADMIN_PLATAFORMA', 'ADMINISTRADOR_MUNICIPAL']}`
- `/gestor/configuracion/dependencias` → misma protección

#### Sidebar (Sidebar.tsx)
- **gestorLiderLinks**: 7 items (sin Dependencias, sin Configuración)
- **adminLinks**: 10 items (incluye Dependencias, Configuración)
- Lógica: `user.roles.includes('GESTOR_LIDER')` para coordinador

### Usuarios de Prueba
- `admin` / `SigemAdmin2026!` → SUPERADMIN_PLATAFORMA
- `lider01` / `GestorLider2026!` → GESTOR_LIDER (creado via API)
- `enemova` / `EneldoGestor2026!` → GESTOR (existente)

### Stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL (Docker puerto 5433)
- Frontend: React 18 + TypeScript + Vite + Tailwind (Docker puerto 3001)
- API: http://localhost:8001/api/v1
- Frontend: http://localhost:3001

### Tests Verificados
- ✅ Coordinador: 7 items en sidebar, bloqueado en /gestor/configuracion y /gestor/configuracion/dependencias
- ✅ Admin: 10 items en sidebar, acceso completo a ambas rutas
- ✅ Login simplificado funciona para ambos roles
- ✅ Build frontend OK, containers healthy

### Vista previa de evidencias (2026-09-30)
- `EvidenciasModal` muestra miniaturas autenticadas para imágenes.
- Imágenes y PDF abren una vista previa ampliada; la descarga original permanece intacta.
- La vista ampliada cierra por botón, fondo o tecla Escape.
- Archivos no compatibles conservan el icono documental y la opción de descarga.
- Prueba Vitest: 3 casos aprobados para imagen, PDF y formato no compatible.
- Build TypeScript/Vite aprobado.
- Docker frontend reconstruido y recreado explícitamente con el bundle actualizado.
- Evidencias reales del Gestor verificadas: listado y descarga autenticada responden HTTP 200.

### Estado de producción (auditoría 2026-09-30)
- **NO autorizado para producción todavía.** Readiness estimado: 2.5/10.
- Bloqueantes: TLS real, backups/restauración, CI/CD, health check HTTP 503 correcto, aprovisionamiento reproducible del rol PostgreSQL y estrategia de rollback.
- Altos: Compose actual es de desarrollo, rate limiting débil, imágenes no reproducibles, falta de límites/hardening, observabilidad ausente y migraciones con credencial privilegiada en runtime.
- La actualización de vista previa está validada para desarrollo, pero el sistema completo requiere resolver estos bloqueos antes de producción.