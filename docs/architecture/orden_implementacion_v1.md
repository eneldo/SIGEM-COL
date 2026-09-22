# Orden de Implementación — Núcleo Central V1

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Objetivo:** Definir el orden exacto de implementación para el Núcleo Central de SIGEM Colombia.

---

## Resumen

El Núcleo Central V1 se implementará en **6 fases secuenciales**. Cada fase debe superar el Quality Gate antes de avanzar a la siguiente.

**Objetivo final del V1:**  
Sistema multi-municipio completo con seguridad, usuarios, roles, permisos, gestores, líneas estratégicas, programas y productos.

---

## Fase 0 — Configuración Inicial (Pre-desarrollo)

**Duración estimada:** 1-2 días  
**Dependencias:** Ninguna

### Objetivo
Configurar el entorno de desarrollo y estructura base del proyecto.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| 0.1 | Inicializar repositorio Git | `.gitignore` | Alta |
| 0.2 | Crear `.env.example` con todas las variables | `.env.example` | Alta |
| 0.3 | Configurar `pyproject.toml` o `requirements.txt` | `src/backend/` | Alta |
| 0.4 | Configurar `package.json` frontend | `src/frontend/` | Alta |
| 0.5 | Crear `docker-compose.yml` básico | `infra/docker/` | Alta |
| 0.6 | Configurar Dockerfile backend | `infra/docker/backend/` | Alta |
| 0.7 | Configurar Dockerfile frontend | `infra/docker/frontend/` | Alta |
| 0.8 | Configurar Alembic | `src/backend/alembic/` | Alta |
| 0.9 | Crear estructura FastAPI básica | `src/backend/main.py` | Alta |
| 0.10 | Verificar que Docker levanta correctamente | - | Alta |

### Entregable
- Proyecto ejecutable con `docker-compose up`
- Backend FastAPI respondiendo en `localhost:8000`
- Frontend React respondiendo en `localhost:3000`
- PostgreSQL y Redis funcionando

### Quality Gate Fase 0
```
[ ] Docker Compose levanta todos los servicios
[ ] Backend responde health check
[ ] Frontend carga correctamente
[ ] PostgreSQL acepta conexiones
[ ] Redis acepta conexiones
[ ] Migraciones Alembic configuradas
[ ] No hay secretos en código
[ ] .gitignore configurado
```

---

## Fase 1 — Núcleo Base (Seguridad)

**Duración estimada:** 5-8 días  
**Dependencias:** Fase 0 completada  
**Resultado esperado:** Núcleo seguro y multi-municipio

### Objetivo
Implementar la base de seguridad completa: municipios, usuarios, roles, permisos, autenticación, auditoría y RLS.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **1.1 Modelos de Base de Datos** | | | |
| 1.1.1 | Modelo `municipios` | `src/backend/models/municipio.py` | Crítica |
| 1.1.2 | Modelo `planes_desarrollo` | `src/backend/models/plan_desarrollo.py` | Crítica |
| 1.1.3 | Modelo `vigencias` | `src/backend/models/vigencia.py` | Crítica |
| 1.1.4 | Modelo `dependencias` | `src/backend/models/dependencia.py` | Crítica |
| 1.1.5 | Modelo `usuarios` | `src/backend/models/usuario.py` | Crítica |
| 1.1.6 | Modelo `roles` | `src/backend/models/rol.py` | Crítica |
| 1.1.7 | Modelo `permisos` | `src/backend/models/permiso.py` | Crítica |
| 1.1.8 | Modelo `usuario_roles` | `src/backend/models/usuario_rol.py` | Crítica |
| 1.1.9 | Modelo `rol_permisos` | `src/backend/models/rol_permiso.py` | Crítica |
| 1.1.10 | Modelo `usuario_dependencias` | `src/backend/models/usuario_dependencia.py` | Crítica |
| 1.1.11 | Modelo `sesiones` | `src/backend/models/sesion.py` | Crítica |
| 1.1.12 | Modelo `intentos_login` | `src/backend/models/intento_login.py` | Crítica |
| 1.1.13 | Modelo `password_history` | `src/backend/models/password_history.py` | Alta |
| 1.1.14 | Modelo `mfa_factors` | `src/backend/models/mfa_factor.py` | Crítica |
| 1.1.15 | Modelo `auditoria_eventos` | `src/backend/models/auditoria_evento.py` | Crítica |
| **1.2 Migraciones** | | | |
| 1.2.1 | Migración inicial tablas | `migrations/versions/001_initial.py` | Crítica |
| 1.2.2 | Migración datos iniciales (roles, permisos) | `migrations/versions/002_seed_data.py` | Crítica |
| 1.2.3 | Configurar RLS en todas las tablas | `migrations/versions/003_rls_policies.py` | Crítica |
| **1.3 Core Backend** | | | |
| 1.3.1 | Configurar base de datos async | `src/backend/core/database.py` | Crítica |
| 1.3.2 | Configurar Redis | `src/backend/core/redis.py` | Alta |
| 1.3.3 | Configurar JWT | `src/backend/core/security.py` | Crítica |
| 1.3.4 | Configurar hashing Argon2id | `src/backend/core/password.py` | Crítica |
| 1.3.5 | Middleware de auditoría | `src/backend/middleware/audit.py` | Crítica |
| 1.3.6 | Middleware de request ID | `src/backend/middleware/request_id.py` | Alta |
| 1.3.7 | Manejador de errores | `src/backend/core/exceptions.py` | Crítica |
| **1.4 Autenticación** | | | |
| 1.4.1 | Servicio de autenticación | `src/backend/services/auth_service.py` | Crítica |
| 1.4.2 | Endpoints login/logout | `src/backend/api/auth/routes.py` | Crítica |
| 1.4.3 | Endpoints cambio contraseña | `src/backend/api/auth/routes.py` | Crítica |
| 1.4.4 | Endpoints MFA (TOTP) | `src/backend/api/auth/mfa/routes.py` | Crítica |
| 1.4.5 | Validación contraseña temporal | `src/backend/services/auth_service.py` | Crítica |
| 1.4.6 | Control de sesiones | `src/backend/services/session_service.py` | Crítica |
| 1.4.7 | Rate limiting login | `src/backend/middleware/rate_limit.py` | Crítica |
| **1.5 Seguridad** | | | |
| 1.5.1 | Servicio de usuarios | `src/backend/services/usuario_service.py` | Crítica |
| 1.5.2 | Servicio de roles | `src/backend/services/rol_service.py` | Crítica |
| 1.5.3 | Servicio de permisos | `src/backend/services/permiso_service.py` | Crítica |
| 1.5.4 | Decorador de permisos | `src/backend/core/permissions.py` | Crítica |
| 1.5.5 | ABAC middleware | `src/backend/middleware/abac.py` | Alta |
| **1.6 Auditoría** | | | |
| 1.6.1 | Servicio de auditoría | `src/backend/services/audit_service.py` | Crítica |
| 1.6.2 | Endpoints consulta auditoría | `src/backend/api/audit/routes.py` | Alta |
| **1.7 API** | | | |
| 1.7.1 | CRUD Municipios | `src/backend/api/municipios/routes.py` | Alta |
| 1.7.2 | CRUD Planes de Desarrollo | `src/backend/api/planes/routes.py` | Alta |
| 1.7.3 | CRUD Dependencias | `src/backend/api/dependencias/routes.py` | Alta |
| 1.7.4 | CRUD Vigencias | `src/backend/api/vigencias/routes.py` | Alta |
| 1.7.5 | CRUD Usuarios (seguridad) | `src/backend/api/security/users/routes.py` | Crítica |
| 1.7.6 | CRUD Roles | `src/backend/api/security/roles/routes.py` | Crítica |
| 1.7.7 | CRUD Permisos | `src/backend/api/security/permissions/routes.py` | Crítica |
| **1.8 Pruebas** | | | |
| 1.8.1 | Tests unitarios modelos | `tests/backend/test_models/` | Alta |
| 1.8.2 | Tests integración auth | `tests/integration/test_auth.py` | Crítica |
| 1.8.3 | Tests RLS | `tests/security/test_rls.py` | Crítica |
| 1.8.4 | Tests aislamiento multi-municipio | `tests/security/test_isolation.py` | Crítica |
| 1.8.5 | Tests auditoría | `tests/integration/test_audit.py` | Alta |

### Quality Gate Fase 1
```
[ ] Todas las migraciones ejecutan correctamente
[ ] RLS configurado en todas las tablas multi-municipio
[ ] Login funciona con JWT
[ ] Contraseña temporal funciona
[ ] Cambio obligatorio funciona
[ ] MFA (TOTP) funciona
[ ] Rate limiting activo
[ ] Auditoría registra eventos
[ ] Tests de aislamiento pasan
[ ] Tests de autorización pasan
[ ] No hay secretos en código
[ ] API documentada con OpenAPI
```

---

## Fase 2 — Gestores Líderes

**Duración estimada:** 5-7 días  
**Dependencias:** Fase 1 completada  
**Resultado esperado:** Módulo completo de gestión de gestores

### Objetivo
Implementar el primer módulo funcional completo: Gestores Líderes con todas las operaciones CRUD, permisos, auditoría y UX especificada.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **2.1 Modelo** | | | |
| 2.1.1 | Modelo `gestores_lideres` | `src/backend/models/gestor_lider.py` | Crítica |
| 2.1.2 | Migración gestores | `migrations/versions/004_gestores.py` | Crítica |
| **2.2 Backend** | | | |
| 2.2.1 | Servicio de gestores | `src/backend/services/gestor_service.py` | Crítica |
| 2.2.2 | Generación código legible (GES-XXXXXX) | `src/backend/services/gestor_service.py` | Crítica |
| 2.2.3 | Sugerencia username automática | `src/backend/services/gestor_service.py` | Crítica |
| 2.2.4 | Generación contraseña temporal segura | `src/backend/services/gestor_service.py` | Crítica |
| 2.2.5 | Asistente por pasos (backend) | `src/backend/api/gestores/routes.py` | Crítica |
| 2.2.6 | CRUD completo endpoints | `src/backend/api/gestores/routes.py` | Crítica |
| 2.2.7 | Endpoints permisos gestor | `src/backend/api/gestores/permissions.py` | Crítica |
| 2.2.8 | Endpoints sesiones gestor | `src/backend/api/gestores/sessions.py` | Alta |
| 2.2.9 | Endpoints auditoría gestor | `src/backend/api/gestores/audit.py` | Alta |
| **2.3 Frontend** | | | |
| 2.3.1 | Asistente por pasos (UI) | `src/frontend/components/gestores/WizardCreacion.tsx` | Crítica |
| 2.3.2 | Paso 1: Identificación | `src/frontend/components/gestores/PasoIdentificacion.tsx` | Crítica |
| 2.3.3 | Paso 2: Cuenta | `src/frontend/components/gestores/PasoCuenta.tsx` | Crítica |
| 2.3.4 | Paso 3: Permisos | `src/frontend/components/gestores/PasoPermisos.tsx` | Crítica |
| 2.3.5 | Paso 4: Seguridad | `src/frontend/components/gestores/PasoSeguridad.tsx` | Crítica |
| 2.3.6 | Tabla de gestores | `src/frontend/components/gestores/TablaGestores.tsx` | Crítica |
| 2.3.7 | Filtros de gestores | `src/frontend/components/gestores/FiltrosGestores.tsx` | Alta |
| 2.3.8 | KPIs del módulo | `src/frontend/components/gestores/KPIs.tsx` | Alta |
| 2.3.9 | Detalle de gestor | `src/frontend/components/gestores/DetalleGestor.tsx` | Alta |
| 2.3.10 | Acciones de gestor | `src/frontend/components/gestores/AccionesGestor.tsx` | Crítica |
| **2.4 Pruebas** | | | |
| 2.4.1 | Tests CRUD gestores | `tests/backend/test_gestores.py` | Crítica |
| 2.4.2 | Tests permisos gestores | `tests/security/test_gestor_permissions.py` | Crítica |
| 2.4.3 | Tests aislamiento gestores | `tests/security/test_gestor_isolation.py` | Crítica |
| 2.4.4 | Tests E2E flujo completo | `tests/e2e/test_gestor_flow.py` | Crítica |

### Quality Gate Fase 2
```
[ ] CRUD de gestores funciona completamente
[ ] Asistente por pasos funciona (4 pasos)
[ ] Código legible generado (GES-XXXXXX)
[ ] Username sugerido automáticamente
[ ] Contraseña temporal generada criptográficamente
[ ] Cambio obligatorio funciona
[ ] Permisos de gestor funcionan
[ ] Auditoría registra acciones de gestor
[ ] Aislamiento multi-municipio verificado
[ ] UI responsive funciona
[ ] Tests E2E pasan
[ ] Documentación actualizada
```

---

## Fase 3 — Líneas Estratégicas

**Duración estimada:** 3-4 días  
**Dependencias:** Fase 1 completada  
**Resultado esperado:** CRUD completo de líneas estratégicas

### Objetivo
Implementar el módulo de Líneas Estratégicas del Plan de Desarrollo.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **3.1 Modelo** | | | |
| 3.1.1 | Modelo `lineas_estrategicas` | `src/backend/models/linea_estrategica.py` | Crítica |
| 3.1.2 | Migración líneas | `migrations/versions/005_lineas_estrategicas.py` | Crítica |
| **3.2 Backend** | | | |
| 3.2.1 | Servicio de líneas | `src/backend/services/linea_service.py` | Crítica |
| 3.2.2 | CRUD endpoints | `src/backend/api/lineas/routes.py` | Crítica |
| 3.2.3 | Validación código único por plan | `src/backend/api/lineas/routes.py` | Crítica |
| **3.3 Frontend** | | | |
| 3.3.1 | Lista de líneas | `src/frontend/pages/lineas/ListaLineas.tsx` | Crítica |
| 3.3.2 | Formulario crear/editar | `src/frontend/pages/lineas/FormLinea.tsx` | Crítica |
| 3.3.3 | Detalle de línea | `src/frontend/pages/lineas/DetalleLinea.tsx` | Alta |
| **3.4 Pruebas** | | | |
| 3.4.1 | Tests CRUD líneas | `tests/backend/test_lineas.py` | Crítica |
| 3.4.2 | Tests permisos | `tests/security/test_linea_permissions.py` | Alta |

### Quality Gate Fase 3
```
[ ] CRUD funciona correctamente
[ ] Código único validado por plan
[ ] RLS activo (solo ve líneas de su municipio)
[ ] Auditoría registra acciones
[ ] UI funcional y responsive
[ ] Tests pasan
```

---

## Fase 4 — Programas

**Duración estimada:** 3-4 días  
**Dependencias:** Fase 3 completada  
**Resultado esperado:** CRUD completo de programas

### Objetivo
Implementar el módulo de Programas vinculados a Líneas Estratégicas.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **4.1 Modelo** | | | |
| 4.1.1 | Modelo `programas` | `src/backend/models/programa.py` | Crítica |
| 4.1.2 | Migración programas | `migrations/versions/006_programas.py` | Crítica |
| **4.2 Backend** | | | |
| 4.2.1 | Servicio de programas | `src/backend/services/programa_service.py` | Crítica |
| 4.2.2 | CRUD endpoints | `src/backend/api/programas/routes.py` | Crítica |
| 4.2.3 | Relación con línea estratégica | `src/backend/api/programas/routes.py` | Crítica |
| **4.3 Frontend** | | | |
| 4.3.1 | Lista de programas | `src/frontend/pages/programas/ListaProgramas.tsx` | Crítica |
| 4.3.2 | Formulario crear/editar | `src/frontend/pages/programas/FormPrograma.tsx` | Crítica |
| 4.3.3 | Detalle de programa | `src/frontend/pages/programas/DetallePrograma.tsx` | Alta |
| **4.4 Pruebas** | | | |
| 4.4.1 | Tests CRUD programas | `tests/backend/test_programas.py` | Crítica |
| 4.4.2 | Tests relación línea-programa | `tests/integration/test_linea_programa.py` | Alta |

### Quality Gate Fase 4
```
[ ] CRUD funciona correctamente
[ ] Relación línea-programa intacta
[ ] RLS activo
[ ] Auditoría registra acciones
[ ] UI funcional y responsive
[ ] Tests pasan
```

---

## Fase 5 — Productos

**Duración estimada:** 4-5 días  
**Dependencias:** Fase 4 completada  
**Resultado esperado:** CRUD completo de productos

### Objetivo
Implementar el módulo de Productos vinculados a Programas, con asignación de gestor responsable y dependencia.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **5.1 Modelo** | | | |
| 5.1.1 | Modelo `productos` | `src/backend/models/producto.py` | Crítica |
| 5.1.2 | Migración productos | `migrations/versions/007_productos.py` | Crítica |
| **5.2 Backend** | | | |
| 5.2.1 | Servicio de productos | `src/backend/services/producto_service.py` | Crítica |
| 5.2.2 | CRUD endpoints | `src/backend/api/productos/routes.py` | Crítica |
| 5.2.3 | Asignación gestor responsable | `src/backend/api/productos/routes.py` | Crítica |
| 5.2.4 | Asignación dependencia | `src/backend/api/productos/routes.py` | Crítica |
| **5.3 Frontend** | | | |
| 5.3.1 | Lista de productos | `src/frontend/pages/productos/ListaProductos.tsx` | Crítica |
| 5.3.2 | Formulario crear/editar | `src/frontend/pages/productos/FormProducto.tsx` | Crítica |
| 5.3.3 | Detalle de producto | `src/frontend/pages/productos/DetalleProducto.tsx` | Alta |
| **5.4 Pruebas** | | | |
| 5.4.1 | Tests CRUD productos | `tests/backend/test_productos.py` | Crítica |
| 5.4.2 | Tests relación programa-producto | `tests/integration/test_programa_producto.py` | Alta |
| 5.4.3 | Tests asignación gestor | `tests/integration/test_producto_gestor.py` | Alta |

### Quality Gate Fase 5
```
[ ] CRUD funciona correctamente
[ ] Relación programa-producto intacta
[ ] Asignación gestor funciona
[ ] Asignación dependencia funciona
[ ] RLS activo
[ ] Auditoría registra acciones
[ ] UI funcional y responsive
[ ] Tests pasan
[ ] Preparado para metas/indicadores (V1.1)
```

---

## Fase 6 — Dashboards

**Duración estimada:** 4-5 días  
**Dependencias:** Fases 2, 3, 4, 5 completadas  
**Resultado esperado:** Dashboards independientes por rol

### Objetivo
Implementar dashboards separados para Administrador Municipal y Gestor Líder, con datos consolidados sin romper aislamiento.

### Tareas

| # | Tarea | Archivos | Prioridad |
|---|-------|----------|-----------|
| **6.1 Backend - Consolidación** | | | |
| 6.1.1 | Servicio de consolidación | `src/backend/services/consolidacion_service.py` | Crítica |
| 6.1.2 | Endpoints estadísticas admin | `src/backend/api/dashboard/admin/routes.py` | Crítica |
| 6.1.3 | Endpoints estadísticas gestor | `src/backend/api/dashboard/gestor/routes.py` | Crítica |
| **6.2 Frontend - Dashboard Admin** | | | |
| 6.2.1 | Layout dashboard admin | `src/frontend/pages/admin/LayoutAdmin.tsx` | Crítica |
| 6.2.2 | KPIs globales | `src/frontend/components/dashboard/admin/KPIsGlobales.tsx` | Crítica |
| 6.2.3 | Resumen municipio | `src/frontend/components/dashboard/admin/ResumenMunicipio.tsx` | Alta |
| 6.2.4 | Listado gestores | `src/frontend/components/dashboard/admin/ListadoGestores.tsx` | Alta |
| 6.2.5 | Alertas admin | `src/frontend/components/dashboard/admin/Alertas.tsx` | Alta |
| **6.3 Frontend - Dashboard Gestor** | | | |
| 6.3.1 | Layout dashboard gestor | `src/frontend/pages/gestor/LayoutGestor.tsx` | Crítica |
| 6.3.2 | KPIs personales | `src/frontend/components/dashboard/gestor/KPIsPersonales.tsx` | Crítica |
| 6.3.3 | Mis productos | `src/frontend/components/dashboard/gestor/MisProductos.tsx` | Crítica |
| 6.3.4 | Mis pendientes | `src/frontend/components/dashboard/gestor/MisPendientes.tsx` | Alta |
| 6.3.5 | Mis alertas | `src/frontend/components/dashboard/gestor/MisAlertas.tsx` | Alta |
| **6.4 Pruebas** | | | |
| 6.4.1 | Tests consolidación datos | `tests/integration/test_consolidacion.py` | Crítica |
| 6.4.2 | Tests aislamiento dashboards | `tests/security/test_dashboard_isolation.py` | Crítica |
| 6.4.3 | Tests E2E dashboards | `tests/e2e/test_dashboards.py` | Alta |

### Quality Gate Fase 6
```
[ ] Dashboard Admin muestra datos consolidados
[ ] Dashboard Gestor muestra solo sus datos
[ ] Aislamiento entre dashboards verificado
[ ] Consolidación no rompe aislamiento
[ ] UI responsive en ambos dashboards
[ ] Tests de aislamiento pasan
[ ] Tests de consolidación pasan
[ ] Documentación actualizada
[ ] CHANGELOG actualizado
```

---

## Quality Gate Final V1

Antes de considerar SIGEM V1 completo:

```
[ ] TODAS las migraciones ejecutan
[ ] TODOS los tests pasan
[ ] RLS verificado en TODAS las tablas
[ ] Aislamiento multi-municipio probado
[ ] Auditoría funciona en TODAS las acciones críticas
[ ] Contraseñas nunca se almacenan en texto plano
[ ] MFA funciona (TOTP mínimo)
[ ] Dashboards separados funcionan
[ ] Consolidación funciona sin romper aislamiento
[ ] UI responsive funciona
[ ] Documentación completa
[ ] CHANGELOG actualizado
[ ] No hay secretos en código
[ ] No hay TODOs críticos
[ ] No hay errores en consola
```

---

## Dependencias entre Fases

```
Fase 0 (Configuración)
    ↓
Fase 1 (Núcleo Base)
    ↓
    ├──→ Fase 2 (Gestores)
    │        ↓
    ├──→ Fase 3 (Líneas) → Fase 4 (Programas) → Fase 5 (Productos)
    │                                                          ↓
    └──────────────────────────────────────────────────────────→ Fase 6 (Dashboards)
```

**Nota:** Las fases 2, 3, 4 y 5 pueden ejecutarse en paralelo después de la Fase 1, pero se recomienda secuencial para mantener calidad.

---

**Documento generado como parte de la auditoría inicial — Sección 62 del MASTER_PROMPT**
