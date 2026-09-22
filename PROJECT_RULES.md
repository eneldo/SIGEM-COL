# PROJECT_RULES — SIGEM Colombia

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Objetivo:** Reglas obligatorias para el desarrollo de SIGEM Colombia.

---

## Reglas Absolutas (NUNCA violar)

### 1. Seguridad

1. **Nunca almacenar secretos en código.** Usar variables de entorno.
2. **Nunca hardcodear municipios.** Siempre usar `municipio_id` de la sesión.
3. **Nunca hardcodear usuarios.** Siempre usar `usuario_id` de la sesión.
4. **Nunca confiar en el frontend para seguridad.** Siempre validar server-side.
5. **Nunca almacenar contraseñas en texto plano.** Usar Argon2id.
6. **Nunca almacenar tokens en logs.** Nunca registrar JWT, MFA secrets.
7. **Nunca almacenar secretos MFA en texto plano.** Cifrar al almacenar.
8. **Nunca usar MD5, SHA1 o SHA256 directo para contraseñas.** Solo Argon2id.
9. **Nunca reutilizar IDs externos (cédula) como PK.** Usar UUIDv7.
10. **Nunca dejar endpoints críticos sin permisos.** Siempre autorizar.

### 2. Integridad de Datos

11. **Nunca eliminar código funcional sin analizar dependencias.** Revisar impacto.
12. **Nunca cambiar arquitectura silenciosamente.** Documentar en decisions.md.
13. **Nunca crear duplicados.** Reutilizar componentes existentes.
14. **Nunca saltarse migraciones.** Siempre usar Alembic.
15. **Nunca ejecutar SQL destructivo sin respaldo.** Siempre respaldar primero.
16. **Nunca borrar históricos auditables.** Usar eliminación lógica.
17. **Nunca sobrescribir datos silenciosamente.** Usar control de concurrencia.

### 3. Calidad

18. **Nunca terminar módulos sin tests.** Cobertura mínima 80%.
19. **Nunca avanzar de fase con errores críticos.** Superar Quality Gate.
20. **Nunca implementar funcionalidad fuera del alcance** antes de asegurar el núcleo.

---

## Reglas de Desarrollo

### 4. Código

1. **Separar responsabilidades:** routes → services → repositories → models
2. **Usar tipado fuerte:** TypeScript en frontend, Python type hints en backend
3. **Validar con Pydantic:** Todos los inputs y outputs
4. **Async/await:** Toda operación de base de datos
5. **No improvisar:** Seguir patrones establecidos

### 5. Base de Datos

1. **RLS obligatorio:** En todas las tablas multi-municipio
2. **Índices en foreign keys:** Siempre
3. **Timestamps:** `created_at`, `updated_at` en todas las tablas
4. **Eliminación lógica:** `deleted_at`, `deleted_by` cuando aplique
5. **UUIDv7:** Como PK principal
6. **Código legible:** Campo `codigo` para usuarios (GES-XXXXXX)

### 6. API

1. **Prefijo versionado:** `/api/v1/`
2. **Errores estructurados:** Formato uniforme
3. **Request ID:** En cada petición
4. **OpenAPI:** Documentación automática
5. **Auditoría:** En acciones críticas

### 7. Frontend

1. **Componentes funcionales:** Con hooks
2. **Formularios controlados:** Validación client y server
3. **Rutas protegidas:** Basadas en permisos
4. **Responsive:** Mobile-first
5. **Accesibilidad:** WCAG 2.2 AA

### 8. Seguridad

1. **Rate limiting:** En endpoints de autenticación
2. **MFA obligatorio:** Para Administradores
3. **Contraseña temporal:** Generada criptográficamente
4. **Cambio obligatorio:** En primer login
5. **Sesiones:** Listar, revocar, expirar

---

## Reglas de Documentación

### 9. Archivos Obligatorios

1. **README.md:** Actualizado
2. **CHANGELOG.md:** Registro de cambios
3. **MASTER_PROMPT.md:** Especificación maestra
4. **AGENTS.md:** Definición de agentes
5. **PROJECT_RULES.md:** Este archivo
6. **ROADMAP.md:** Hoja de ruta

### 10. Por Módulo

1. **Especificación:** En `specs/`
2. **Documentación técnica:** En `docs/`
3. **Tests:** En `tests/`
4. **Migraciones:** En `migrations/`

---

## Reglas de Seguridad

### 11. Autenticación

1. **JWT:** Con expiración corta (15 min access, 7 días refresh)
2. **Argon2id:** Para hashing de contraseñas
3. **Contraseña temporal:** 20+ caracteres, expira en 24h
4. **Cambio obligatorio:** En primer login
5. **MFA:** TOTP mínimo, WebAuthn ideal

### 12. Autorización

1. **RBAC:** Roles predefinidos
2. **ABAC:** Basado en atributos (municipio, dependencia)
3. **RLS:** Aislamiento a nivel de base de datos
4. **Principio de mínimo privilegio:** Solo lo necesario

### 13. Auditoría

1. **Todo evento de seguridad:** Login, logout, cambio password, MFA
2. **Toda acción crítica:** Crear, editar, eliminar
3. **Metadata completa:** IP, user agent, timestamp, actor
4. **Retención:** Mínimo 1 año

---

## Reglas de Pruebas

### 14. Cobertura

1. **Mínimo 80%:** Cobertura de código
2. **Tests unitarios:** Lógica de negocio
3. **Tests integración:** API + base de datos
4. **Tests seguridad:** Autorización, RLS, aislamiento
5. **Tests E2E:** Flujos críticos completos

### 15. Aislamiento

1. **Multi-municipio:** Usuario A no ve datos de Municipio B
2. **Manipulación de IDs:** Probar con IDs ajenos
3. **Manipulación de URL:** Probar endpoints directos
4. **Requests directos:** Sin pasar por frontend

---

## Reglas de Deploy

### 16. Infraestructura

1. **Docker:** Todos los servicios en contenedores
2. **HTTPS:** Obligatorio en producción
3. **Health checks:** En todos los servicios
4. **Backups:** Automatizados y probados
5. **Logs estructurados:** Para monitoreo

### 17. Producción

1. **Secretos:** Nunca en repositorio
2. **Rate limiting:** Activo
3. **MFA:** Obligatorio para admins
4. **Auditoría:** Activa
5. **Monitoreo:** Básico

---

## Infracción de Reglas

Cualquier infracción a estas reglas debe ser:

1. **Detectada:** En code review o testing
2. **Documentada:** En `context/decisions.md`
3. **Corregida:** Antes de avanzar
4. **Prevenida:** Con test o lint rule

---

## Excepciones

Las excepciones a estas reglas deben ser:

1. **Justificadas:** Documentando por qué
2. **Aprobadas:** Por el Architect Agent
3. **Temporal:** Con fecha de revisión
4. **Registradas:** En `context/decisions.md`

---

**Documento generado como parte de la auditoría inicial — Sección 62 del MASTER_PROMPT**
