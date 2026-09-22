# Agents — SIGEM Colombia

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Objetivo:** Definición de agentes especializados para desarrollo de SIGEM Colombia.

---

## Descripción

SIGEM Colombia será desarrollado utilizando agentes especializados, cada uno responsable de un dominio específico del sistema. Esta separación garantiza calidad, consistencia y trazabilidad.

---

## Agentes Definidos

### 1. Architect Agent

**Responsable:** Arquitectura del sistema

**Funciones:**
- Definir y mantener arquitectura modular
- Gestionar dependencias entre componentes
- Establecer patrones de diseño
- Crear Architecture Decision Records (ADRs)
- Revisar cambios arquitectónicos
- Validar escalabilidad y mantenibilidad

**Archivos a cargo:**
- `docs/architecture/`
- `context/architecture_context.md`
- `context/decisions.md`

**Herramientas:**
- Diagramas de arquitectura
- Análisis de dependencias
- Revisión de código arquitectónico

---

### 2. Backend Agent

**Responsable:** Desarrollo del servidor y API

**Funciones:**
- Implementar endpoints REST con FastAPI
- Crear servicios y repositorios
- Implementar lógica de negocio
- Configurar autenticación y autorización
- Implementar middleware
- Crear schemas Pydantic

**Archivos a cargo:**
- `src/backend/`
- `tests/backend/`
- `tests/integration/`

**Stack:**
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic

**Convenciones:**
- Separación: routes → services → repositories → models
- Validación con Pydantic
- Tipado fuerte
- Async/await en toda la capa de acceso a datos

---

### 3. Frontend Agent

**Responsable:** Desarrollo de interfaz de usuario

**Funciones:**
- Implementar componentes React
- Crear páginas y dashboards
- Implementar formularios
- Gestionar estado de aplicación
- Implementar routing protegido
- Crear UI responsive y accesible

**Archivos a cargo:**
- `src/frontend/`
- `tests/frontend/`

**Stack:**
- React 18+
- TypeScript
- Vite

**Convenciones:**
- Componentes funcionales con hooks
- Separación: pages → components → hooks → services
- Formularios controlados
- Accesibilidad WCAG 2.2 AA
- Responsive design

---

### 4. Database Agent

**Responsable:** Base de datos y migraciones

**Funciones:**
- Diseñar esquema de base de datos
- Crear migraciones con Alembic
- Implementar Row-Level Security (RLS)
- Optimizar índices y queries
- Mantener integridad referencial
- Documentar esquema

**Archivos a cargo:**
- `migrations/`
- `src/backend/models/`
- `docs/database/`

**Herramientas:**
- PostgreSQL 17+
- Alembic
- pgAdmin / DBeaver

**Convenciones:**
- Migraciones reversibles cuando sea posible
- RLS en todas las tablas multi-municipio
- Índices en foreign keys
- Eliminación lógica (soft delete)
- Timestamps en todas las tablas

---

### 5. Security Agent

**Responsable:** Seguridad de la aplicación

**Funciones:**
- Realizar threat modeling
- Implementar autenticación segura
- Configurar autorización (RBAC/ABAC)
- Implementar MFA
- Realizar auditorías de seguridad
- Implementar Rate Limiting
- Revisar vulnerabilidades

**Archivos a cargo:**
- `security/`
- `docs/security/`
- `tests/security/`

**Herramientas:**
- OWASP guidelines
- Bandit (Python security linter)
- Safety (dependency vulnerabilities)

**Convenciones:**
- Nunca almacenar secretos en código
- Argon2id para contraseñas
- JWT con expiración corta
- MFA obligatorio para admins
- Auditoría completa de acciones

---

### 6. QA Agent

**Responsable:** Calidad y pruebas

**Funciones:**
- Crear tests unitarios
- Crear tests de integración
- Crear tests E2E
- Implementar tests de seguridad
- Medir cobertura de código
- Detectar regresiones

**Archivos a cargo:**
- `tests/`
- Configuración de testing

**Herramientas:**
- Pytest (backend)
- Jest/Vitest (frontend)
- Playwright (E2E)
- Coverage.py

**Convenciones:**
- TDD cuando sea viable
- Mínimo 80% cobertura
- Tests de aislamiento multi-municipio
- Tests de autorización obligatorios
- No tests dependientes de estado

---

### 7. DevOps Agent

**Responsable:** Infraestructura y despliegue

**Funciones:**
- Configurar Docker y Docker Compose
- Configurar Nginx reverse proxy
- Implementar CI/CD
- Configurar monitoreo
- Gestionar backups
- Implementar health checks

**Archivos a cargo:**
- `infra/`
- `scripts/`
- `.github/workflows/` (futuro)

**Herramientas:**
- Docker / Docker Compose
- Nginx
- GitHub Actions (futuro)
- Prometheus/Grafana (futuro)

**Convenciones:**
- Infraestructura como código
- Health checks en todos los servicios
- Backups automatizados
- Logs estructurados
- HTTPS obligatorio en producción

---

### 8. Documentation Agent

**Responsable:** Documentación del proyecto

**Funciones:**
- Mantener README actualizado
- Documentar API (OpenAPI)
- Crear guías de usuario
- Mantener CHANGELOG
- Documentar decisiones técnicas
- Crear especificaciones

**Archivos a cargo:**
- `docs/`
- `README.md`
- `CHANGELOG.md`
- `specs/`

**Convenciones:**
- Documentación viva (se actualiza con código)
- OpenAPI auto-generado desde FastAPI
- Especificaciones antes de implementar
- CHANGELOG siguiendo Keep a Changelog

---

## Coordinación entre Agentes

### Flujo de Trabajo

```
Architect → Define estructura y patrones
    ↓
Database → Diseña esquema y migraciones
    ↓
Security → Implementa autenticación y autorización
    ↓
Backend → Implementa API y lógica de negocio
    ↓
Frontend → Implementa interfaz de usuario
    ↓
QA → Prueba toda la implementación
    ↓
DevOps → Configura infraestructura
    ↓
Documentation → Documenta todo
```

### Reglas de Comunicación

1. **Antes de modificar código existente:**
   - Revisar MASTER_PROMPT.md
   - Revisar PROJECT_RULES.md
   - Inspeccionar código afectado
   - Identificar dependencias

2. **Al implementar nuevo módulo:**
   - Crear especificación primero
   - Aprobar con Architect
   - Implementar Backend
   - Implementar Frontend
   - Crear pruebas
   - Documentar

3. **Al detectar problema de seguridad:**
   - Bloquear avance
   - Documentar en context/decisions.md
   - Resolver antes de continuar

---

## Uso en OpenCode

Cada agente será invocado según la tarea:

```bash
# Ejemplo: implementar módulo de gestores
# 1. Architect define estructura
# 2. Database crea migración
# 3. Security implementa permisos
# 4. Backend implementa API
# 5. Frontend implementa UI
# 6. QA crea pruebas
# 7. Documentation actualiza docs
```

---

**Documento generado como parte de la auditoría inicial — Sección 62 del MASTER_PROMPT**
