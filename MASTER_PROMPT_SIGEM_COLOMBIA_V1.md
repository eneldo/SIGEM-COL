# MASTER PROMPT — SIGEM COLOMBIA
## Núcleo Central V1 — Seguimiento al Plan de Desarrollo Municipal

**Versión:** 1.0  
**Objetivo:** Construcción del Núcleo Central de SIGEM Colombia para seguimiento, medición, control de cumplimiento y generación de informes sobre las metas del Plan de Desarrollo Municipal.  
**Entorno objetivo:** OpenCode + ChatGPT / IA de apoyo  
**Arquitectura base:** Monolito modular, multi-municipio, API-first, segura, auditable y escalable.

---

# 1. ROL DE LA IA

Actúa como un equipo senior compuesto por:

- Arquitecto de software.
- Ingeniero backend.
- Ingeniero frontend.
- Ingeniero DevSecOps.
- DBA PostgreSQL.
- Especialista en seguridad de aplicaciones.
- Especialista en auditoría y trazabilidad.
- Analista funcional de sistemas públicos.
- Diseñador UX/UI institucional.
- QA Automation Engineer.

Tu responsabilidad es analizar, diseñar, implementar, probar y documentar SIGEM Colombia siguiendo estrictamente este contrato.

No debes improvisar cambios arquitectónicos importantes sin documentarlos primero.

Antes de modificar código existente:

1. inspecciona el repositorio;
2. identifica arquitectura, dependencias y convenciones;
3. revisa README.md;
4. revisa MASTER_PROMPT.md;
5. revisa AGENTS.md;
6. revisa PROJECT_RULES.md;
7. revisa ROADMAP.md;
8. revisa specs/;
9. revisa context/;
10. revisa migrations/ existentes;
11. identifica deuda técnica;
12. evita duplicar componentes, modelos, rutas o servicios existentes.

---

# 2. OBJETIVO GENERAL

Construir un sistema institucional orientado a:

- hacer seguimiento al Plan de Desarrollo Municipal;
- medir avances;
- controlar cumplimiento;
- gestionar responsables;
- administrar líneas estratégicas;
- administrar programas;
- administrar productos;
- registrar indicadores;
- gestionar metas;
- registrar avances;
- cargar evidencias;
- auditar todas las acciones;
- consolidar información;
- generar indicadores;
- producir informes de gestión;
- soportar múltiples municipios;
- garantizar aislamiento seguro de información.

SIGEM Colombia no debe quedar limitado a una única alcaldía.

---

# 3. PRINCIPIOS ARQUITECTÓNICOS

Aplicar obligatoriamente:

- arquitectura modular;
- separación de responsabilidades;
- API-first;
- multi-tenant / multi-municipio;
- seguridad por diseño;
- auditoría por diseño;
- principio de mínimo privilegio;
- defensa en profundidad;
- RBAC;
- ABAC;
- PostgreSQL Row-Level Security;
- eliminación lógica;
- versionado de evidencias;
- trazabilidad completa;
- validación server-side;
- tipado fuerte;
- pruebas automatizadas;
- migraciones controladas;
- documentación viva.

No iniciar con microservicios.

Construir inicialmente como **monolito modular desacoplado**, preparado para una futura separación de servicios.

---

# 4. STACK BASE RECOMENDADO

## Backend

- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL 17+
- Redis
- JWT o sesiones seguras según arquitectura definida
- Argon2id para hashing de contraseñas
- WebAuthn / Passkeys
- TOTP como alternativa MFA
- OpenAPI

## Frontend

Preferencia:

- React
- TypeScript
- Vite o Next.js según arquitectura existente
- componentes reutilizables;
- validación de formularios;
- control de sesión;
- rutas protegidas;
- separación de dashboards por rol.

## Infraestructura

- Docker
- Docker Compose
- Nginx / reverse proxy
- HTTPS obligatorio en producción
- PostgreSQL
- Redis
- almacenamiento de evidencias
- backups automáticos

---

# 5. ESTRUCTURA BASE DEL REPOSITORIO

Mantener esta estructura como contrato organizacional:

```text
SIGEM_COLOMBIA/
│
├── README.md
├── MASTER_PROMPT.md
├── AGENTS.md
├── PROJECT_RULES.md
├── ROADMAP.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
│
├── agents/
│   ├── architect.md
│   ├── backend.md
│   ├── frontend.md
│   ├── database.md
│   ├── security.md
│   ├── qa.md
│   ├── devops.md
│   └── documentation.md
│
├── context/
│   ├── project_context.md
│   ├── business_context.md
│   ├── architecture_context.md
│   ├── security_context.md
│   ├── database_context.md
│   ├── ui_context.md
│   └── decisions.md
│
├── orchestration/
│   ├── workflow.md
│   ├── execution_order.md
│   ├── quality_gates.md
│   ├── release_process.md
│   └── review_checklist.md
│
├── roles/
│   ├── superadmin.md
│   ├── administrador_municipal.md
│   ├── gestor_lider.md
│   ├── auditor.md
│   └── consulta.md
│
├── specs/
│   ├── core/
│   ├── auth/
│   ├── gestores/
│   ├── seguridad/
│   ├── lineas_estrategicas/
│   ├── programas/
│   ├── productos/
│   ├── auditoria/
│   ├── evidencias/
│   └── dashboards/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── security/
│   ├── ui/
│   ├── deployment/
│   └── user_guides/
│
├── src/
│   ├── backend/
│   └── frontend/
│
├── tests/
│   ├── backend/
│   ├── frontend/
│   ├── integration/
│   ├── security/
│   └── e2e/
│
├── migrations/
│
├── scripts/
│   ├── setup/
│   ├── database/
│   ├── maintenance/
│   └── backup/
│
├── infra/
│   ├── docker/
│   ├── nginx/
│   ├── postgres/
│   ├── redis/
│   └── deployment/
│
└── security/
    ├── policies/
    ├── threat-model/
    ├── checklists/
    ├── incident-response/
    └── hardening/
```

No crear carpetas arbitrarias fuera de esta estructura sin justificarlo.

---

# 6. NÚCLEO CENTRAL V1

El Núcleo Central del Administrador Municipal tendrá inicialmente:

1. Dashboard Administrador
2. Gestores Líderes
3. Líneas Estratégicas
4. Programas
5. Productos
6. Seguridad

## Seguridad

El módulo Seguridad debe contener:

- Configuración
- Usuarios
- Roles
- Permisos
- Auditoría
- Auditoría de evidencias

Además, como maestros internos:

- Municipios
- Planes de Desarrollo
- Vigencias
- Dependencias

---

# 7. MODELO JERÁRQUICO PRINCIPAL

La estructura funcional debe respetar:

```text
Municipio
   ↓
Plan de Desarrollo
   ↓
Línea Estratégica
   ↓
Programa
   ↓
Producto
   ↓
Meta
   ↓
Indicador
   ↓
Avance
   ↓
Evidencia
```

En V1 se implementará inicialmente hasta Producto, pero la arquitectura de datos debe quedar preparada para Meta, Indicador, Avance y Evidencia.

---

# 8. MULTI-MUNICIPIO

SIGEM Colombia debe ser multi-municipio desde el núcleo.

Toda entidad funcional relevante debe relacionarse con:

```text
municipio_id
```

o:

```text
tenant_id
```

Seleccionar una sola convención y utilizarla en todo el proyecto.

Preferencia:

```text
municipio_id
```

El aislamiento debe aplicarse:

- frontend;
- backend;
- servicios;
- repositorios;
- consultas;
- base de datos;
- PostgreSQL RLS.

Nunca confiar únicamente en filtros del frontend.

---

# 9. ROLES BASE

Crear inicialmente:

## Superadministrador Plataforma

Responsable técnico global de SIGEM.

## Administrador Municipal

Puede ser:

- Alcalde;
- funcionario delegado;
- administrador autorizado.

Administra exclusivamente su municipio.

## Gestor Líder

Responsable de dependencias, productos, metas y avances asignados.

## Auditor

Rol preparado para fases posteriores.

## Consulta

Rol de solo lectura.

No hardcodear nombres de personas ni cargos específicos.

---

# 10. MÓDULO GESTORES LÍDERES

Este será el primer módulo funcional completo del Núcleo Central.

Debe permitir:

- crear gestor;
- consultar gestor;
- editar gestor;
- administrar permisos;
- asignar dependencias;
- activar;
- desactivar;
- bloquear;
- desbloquear;
- restablecer contraseña;
- revocar sesiones;
- consultar auditoría;
- consultar último acceso;
- consultar IP;
- consultar intentos fallidos;
- realizar eliminación lógica.

---

# 11. ALTA DE GESTOR — FLUJO UX

No usar un formulario plano excesivamente largo.

Implementar preferentemente un asistente por pasos.

## Paso 1 — Identificación

Capturar:

- nombre completo;
- correo institucional;
- teléfono;
- cargo;
- dependencia principal;
- dependencias adicionales.

## Paso 2 — Cuenta

Generar o definir:

- UUID interno;
- código visible;
- nombre de usuario;
- rol;
- municipio;
- estado.

## Paso 3 — Permisos

Configurar:

- dependencias;
- líneas estratégicas;
- programas;
- productos;
- permisos especiales.

## Paso 4 — Seguridad

Configurar:

- contraseña temporal;
- cambio obligatorio;
- MFA;
- revisión final;
- confirmación.

---

# 12. IDENTIFICADORES

No utilizar enteros secuenciales como identificador primario expuesto.

Usar preferentemente:

```text
UUIDv7
```

Crear adicionalmente un código legible.

Ejemplo:

```text
GES-000001
GES-000002
GES-000003
```

Separar:

```text
id
codigo
```

`id` será técnico.

`codigo` será visible al usuario.

---

# 13. NOMBRE DE USUARIO

El sistema debe sugerir nombre de usuario automáticamente.

Ejemplo:

```text
Juan Carlos Pérez
→ jperez
```

Si existe:

```text
jperez2
```

Garantizar unicidad dentro del municipio:

```text
UNIQUE (municipio_id, username_normalizado)
```

No utilizar cédula como username.

---

# 14. CONTRASEÑAS

El Administrador NO debe escribir manualmente la contraseña temporal.

El sistema debe generarla utilizando un generador criptográficamente seguro.

Requisitos:

- temporal;
- aleatoria;
- mínimo 20 caracteres recomendado;
- no almacenarla en texto plano;
- mostrarla una sola vez;
- permitir copiarla;
- registrar únicamente evento de generación;
- almacenar solo hash;
- marcar:

```text
must_change_password = true
```

- establecer expiración;
- revocarla después del cambio definitivo.

Hash recomendado:

```text
Argon2id
```

Nunca utilizar:

- MD5;
- SHA1;
- SHA256 directo;
- cifrado reversible como sustituto de hashing.

---

# 15. CAMBIO OBLIGATORIO DE CONTRASEÑA

Mientras:

```text
must_change_password = true
```

el usuario no puede acceder a módulos funcionales.

Permitir únicamente endpoints equivalentes a:

```text
/auth/me
/auth/change-initial-password
/auth/logout
/auth/mfa/*
```

Luego del cambio:

```text
must_change_password = false
```

Registrar auditoría.

---

# 16. POLÍTICA DE CONTRASEÑA DEL USUARIO

Utilizar una política basada en seguridad moderna.

Preferencia:

- mínimo 15 caracteres;
- permitir frases largas;
- permitir espacios;
- máximo mínimo soportado: 64 caracteres o más;
- no exigir reglas absurdas de composición;
- impedir contraseñas comprometidas;
- impedir username;
- impedir nombre del usuario;
- impedir municipio;
- impedir datos evidentes.

Mostrar ayuda visual:

```text
✓ mínimo requerido
✓ contraseña no comprometida
✓ no contiene datos personales conocidos
✓ confirmación correcta
```

---

# 17. MFA

Implementar MFA.

Prioridad:

1. WebAuthn / Passkeys
2. TOTP
3. códigos de recuperación

Para Administrador Municipal:

```text
MFA obligatorio
```

Para Gestores Líderes:

preferentemente obligatorio.

Registrar:

- fecha configuración;
- método;
- revocaciones;
- recuperación;
- cambios.

Nunca almacenar secretos MFA en texto plano.

---

# 18. CONTROL DE ACCESO

Implementar tres capas:

## RBAC

Determina:

```text
qué acción puede realizar el usuario
```

Ejemplos:

```text
gestor.crear
gestor.ver
gestor.editar
gestor.eliminar
gestor.permisos
producto.ver
producto.editar
auditoria.ver
```

## ABAC

Determina:

```text
sobre qué recurso puede actuar
```

Ejemplos:

- municipio;
- dependencia;
- programa;
- producto;
- gestor asignado.

## PostgreSQL RLS

Determina:

```text
qué filas puede leer o modificar realmente
```

La seguridad no puede depender únicamente del frontend.

---

# 19. SEPARACIÓN DE DASHBOARDS

Crear dashboards distintos.

## Administrador

Ruta conceptual:

```text
/admin/dashboard
```

Debe poder visualizar:

- municipio completo;
- plan de desarrollo;
- líneas estratégicas;
- programas;
- productos;
- gestores;
- indicadores consolidados;
- alertas;
- auditoría;
- seguridad.

## Gestor Líder

Ruta conceptual:

```text
/gestor/dashboard
```

Debe visualizar exclusivamente:

- mi gestión;
- mis dependencias;
- mis productos;
- mis metas;
- mis indicadores;
- mis avances;
- mis evidencias;
- mis alertas;
- mis pendientes.

No debe poder visualizar:

- seguridad global;
- usuarios de otros ámbitos;
- información operativa de otros gestores;
- recursos no asignados.

---

# 20. CONSOLIDACIÓN DE INDICADORES

La separación de permisos NO debe impedir consolidar información.

Implementar capa de agregación.

Conceptualmente:

```text
Gestor A ─┐
Gestor B ─┼──> Avances ──> Motor de indicadores ──> Dashboard Administrador
Gestor C ─┘
```

Cada Gestor modifica únicamente sus recursos.

El sistema consolida datos para:

- programa;
- línea estratégica;
- plan de desarrollo;
- municipio.

---

# 21. ESTADOS DEL USUARIO

Soportar:

```text
PENDIENTE_ACTIVACION
ACTIVO
INACTIVO
BLOQUEADO
SUSPENDIDO
ELIMINADO_LOGICAMENTE
```

Evitar simples booleanos cuando el estado tenga significado operacional.

---

# 22. ELIMINACIÓN LÓGICA

Nunca borrar físicamente usuarios o registros con trazabilidad administrativa.

Implementar campos como:

```text
deleted_at
deleted_by
is_deleted
```

o patrón equivalente.

Toda eliminación debe:

1. pedir confirmación;
2. verificar permisos;
3. validar dependencias;
4. registrar auditoría;
5. invalidar sesiones cuando aplique.

---

# 23. AUDITORÍA DE ACCESO

Por usuario registrar:

```text
ultimo_acceso
ip_ultimo_acceso
user_agent
intentos_fallidos
ultimo_intento_fallido
ultimo_cambio_password
mfa_activo
sesiones_activas
fecha_bloqueo
motivo_bloqueo
```

No confiar únicamente en campos acumulados.

Crear además un historial de eventos.

---

# 24. EVENTOS DE SEGURIDAD

Registrar al menos:

```text
LOGIN_OK
LOGIN_FAILED
LOGOUT
PASSWORD_CHANGED
PASSWORD_RESET
PASSWORD_TEMPORARY_GENERATED
MFA_ENABLED
MFA_DISABLED
ACCOUNT_BLOCKED
ACCOUNT_UNLOCKED
SESSION_REVOKED
ROLE_CHANGED
PERMISSIONS_CHANGED
USER_CREATED
USER_UPDATED
USER_DEACTIVATED
USER_DELETED_LOGICALLY
```

Cada evento debe registrar cuando corresponda:

- usuario;
- actor;
- municipio;
- fecha;
- IP;
- user agent;
- resultado;
- recurso;
- identificador;
- metadata segura.

---

# 25. RATE LIMIT Y PROTECCIÓN DE LOGIN

Implementar:

- rate limiting;
- login throttling;
- bloqueo progresivo;
- protección contra credential stuffing;
- protección contra enumeración de usuarios;
- mensajes de error genéricos;
- detección de comportamiento sospechoso.

Ejemplo:

No decir:

```text
El usuario existe pero la contraseña es incorrecta
```

Usar:

```text
Credenciales inválidas
```

---

# 26. SESIONES

Las sesiones deben poder:

- listarse;
- invalidarse individualmente;
- invalidarse globalmente;
- expirar;
- revocarse después de cambio de password;
- revocarse después de cambio crítico de permisos.

Registrar:

- IP;
- dispositivo;
- fecha creación;
- última actividad;
- expiración.

---

# 27. MÓDULO LÍNEAS ESTRATÉGICAS

CRUD completo.

Campos mínimos:

```text
id
codigo
municipio_id
plan_desarrollo_id
nombre
descripcion
orden
estado
created_at
created_by
updated_at
updated_by
deleted_at
```

Validar códigos únicos por Plan de Desarrollo.

---

# 28. MÓDULO PROGRAMAS

Relación:

```text
Línea Estratégica 1:N Programas
```

Campos mínimos:

```text
id
codigo
municipio_id
linea_estrategica_id
nombre
descripcion
estado
created_at
created_by
updated_at
updated_by
deleted_at
```

---

# 29. MÓDULO PRODUCTOS

Relación:

```text
Programa 1:N Productos
```

Campos mínimos:

```text
id
codigo
municipio_id
programa_id
nombre
descripcion
unidad_medida
dependencia_responsable_id
gestor_lider_id
estado
created_at
created_by
updated_at
updated_by
deleted_at
```

Dejar preparado para:

```text
metas
indicadores
avance
evidencias
```

---

# 30. AUDITORÍA DE EVIDENCIAS

Toda evidencia debe registrar:

```text
id
municipio_id
producto_id
meta_id
usuario_id
nombre_original
nombre_almacenado
mime_type
extension
size
sha256
version
fecha_carga
ip_carga
estado
revisado_por
fecha_revision
observaciones
created_at
updated_at
```

Una evidencia no debe sobrescribirse.

Si se actualiza:

```text
versión 1
versión 2
versión 3
```

Mantener todas las versiones.

---

# 31. SEGURIDAD DE ARCHIVOS

Aplicar:

- lista blanca de extensiones;
- validación MIME;
- validación magic bytes;
- tamaño máximo;
- renombrado interno seguro;
- hash SHA-256;
- prevención path traversal;
- no ejecutar archivos;
- almacenamiento fuera del web root;
- antivirus si infraestructura lo permite;
- auditoría de carga;
- control de descargas.

---

# 32. MODELO DE DATOS INICIAL

Crear inicialmente, como mínimo:

```text
municipios
planes_desarrollo
vigencias
dependencias

usuarios
gestores_lideres
roles
permisos

usuario_roles
rol_permisos
usuario_dependencias

lineas_estrategicas
programas
productos

sesiones
intentos_login
password_history
mfa_factors

auditoria_eventos
auditoria_evidencias
```

Dejar arquitectura preparada para:

```text
metas
indicadores
avances
evidencias
```

---

# 33. CAMPOS TRANSVERSALES

Las entidades relevantes deben manejar:

```text
id
municipio_id
created_at
created_by
updated_at
updated_by
version
estado
deleted_at
deleted_by
```

No repetir `municipio_id` en tablas estrictamente globales.

---

# 34. CONCURRENCIA

Para registros susceptibles a edición simultánea utilizar control optimista.

Ejemplo:

```text
version
```

Si dos usuarios editan el mismo recurso:

```text
409 Conflict
```

No sobrescribir silenciosamente.

---

# 35. API

Todas las APIs deben:

- utilizar `/api/v1`;
- aplicar validación;
- devolver errores estructurados;
- documentarse con OpenAPI;
- verificar autenticación;
- verificar autorización;
- respetar RLS;
- auditar acciones críticas.

Ejemplo:

```text
/api/v1/gestores
/api/v1/lineas-estrategicas
/api/v1/programas
/api/v1/productos
/api/v1/security/users
/api/v1/security/roles
/api/v1/security/permissions
/api/v1/audit/events
```

---

# 36. FORMATO DE ERROR

Usar un contrato uniforme.

Ejemplo:

```json
{
  "error": {
    "code": "GESTOR_NOT_FOUND",
    "message": "El recurso solicitado no está disponible.",
    "details": null,
    "request_id": "..."
  }
}
```

Nunca exponer:

- stack trace;
- SQL;
- secretos;
- configuración interna;
- nombres sensibles de infraestructura.

---

# 37. UX DEL MÓDULO GESTORES

Pantalla principal:

## KPIs

- Total gestores
- Activos
- Inactivos
- Bloqueados
- Intentos fallidos recientes

## Tabla

Columnas recomendadas:

- ID
- Gestor
- Usuario
- Cargo
- Dependencia
- Rol
- Estado
- Último acceso
- IP
- Intentos fallidos
- MFA
- Acciones

## Filtros

- nombre;
- usuario;
- dependencia;
- cargo;
- rol;
- estado.

---

# 38. ACCIONES DE GESTOR

Implementar:

```text
Ver detalles
Editar
Administrar permisos
Cambiar dependencias
Restablecer contraseña
Desbloquear cuenta
Activar
Desactivar
Ver auditoría
Ver sesiones
Revocar sesiones
Eliminar lógicamente
```

Toda acción crítica requiere:

- permiso;
- confirmación;
- auditoría.

---

# 39. PALETA VISUAL OFICIAL

Tomar exclusivamente los colores definidos para el proyecto.

```css
--pine: #0F3D3B;
--pine-deep: #0A2B29;
--forest: #1F6F54;
--forest-soft: #E7EFE9;

--paper: #F5F3EC;
--paper-raised: #FFFFFF;

--ink: #26241F;
--ink-soft: #5B5A54;
--ink-faint: #8B887C;

--line: #DFDACB;

--ochre: #B9852F;
--ochre-deep: #8F6620;
--ochre-soft: #F5E9D4;

--done: #3E7C5A;
--warn: #B5502E;
--warn-soft: #F6E4DA;
```

Usar esta paleta como identidad del sistema.

No copiar datos, textos o estructura funcional de prototipos externos.

---

# 40. DISEÑO RESPONSIVE

La aplicación debe funcionar en:

- escritorio;
- laptop;
- tablet;
- móvil.

Prioridad operativa:

1. escritorio;
2. laptop;
3. tablet;
4. móvil.

Las tablas deben transformarse adecuadamente en dispositivos pequeños.

No usar tablas horizontales imposibles de consultar.

---

# 41. ACCESIBILIDAD

Aplicar:

- etiquetas semánticas;
- labels;
- navegación por teclado;
- foco visible;
- contraste suficiente;
- aria-label donde aplique;
- mensajes de error accesibles;
- soporte para lectores de pantalla.

Objetivo:

```text
WCAG 2.2 AA
```

cuando sea viable.

---

# 42. PRUEBAS

No considerar terminado ningún módulo sin pruebas.

## Backend

- unit tests;
- integration tests;
- authorization tests;
- RLS tests;
- validation tests;
- security tests.

## Frontend

- component tests;
- form tests;
- permissions tests;
- route guard tests.

## E2E

Casos obligatorios:

1. Administrador crea Gestor.
2. Gestor recibe contraseña temporal.
3. Gestor inicia sesión.
4. Sistema obliga cambio de contraseña.
5. Sistema obliga/configura MFA.
6. Gestor entra a su dashboard.
7. Gestor intenta consultar recurso ajeno.
8. API devuelve acceso denegado.
9. Administrador consulta auditoría.
10. Administrador revoca sesión.

---

# 43. PRUEBAS DE AISLAMIENTO

Crear pruebas específicas.

Ejemplo:

Municipio A:

```text
usuario_A
producto_A
```

Municipio B:

```text
usuario_B
producto_B
```

Validar:

```text
usuario_A NO puede consultar producto_B
usuario_B NO puede consultar producto_A
```

Incluso:

- manipulando IDs;
- manipulando URL;
- enviando requests directos;
- saltándose frontend.

---

# 44. MIGRACIONES

Toda modificación de base de datos debe utilizar Alembic.

No modificar manualmente producción.

Cada migración debe:

- tener nombre claro;
- indicar dependencia;
- permitir upgrade;
- permitir downgrade cuando sea razonablemente posible;
- evitar pérdida accidental de datos.

---

# 45. LOGGING

Usar logs estructurados.

Registrar:

- request_id;
- timestamp;
- endpoint;
- método;
- usuario;
- municipio;
- status;
- duración.

No registrar:

- passwords;
- tokens;
- secretos;
- MFA secrets;
- documentos completos;
- PII innecesaria.

---

# 46. BACKUPS

Preparar infraestructura para:

- backup PostgreSQL;
- backup evidencias;
- cifrado;
- retención;
- restauración;
- pruebas periódicas de restore.

Un backup que nunca se prueba no se considera confiable.

---

# 47. CONFIGURACIÓN

Nunca almacenar secretos en código.

Usar variables de entorno.

Crear:

```text
.env.example
```

sin valores reales.

Variables sugeridas:

```text
APP_ENV
APP_NAME
DATABASE_URL
REDIS_URL

SECRET_KEY
JWT_SECRET_KEY

FRONTEND_URL
BACKEND_URL

PASSWORD_HASH_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

MFA_ISSUER

STORAGE_PATH
MAX_UPLOAD_SIZE_MB

RATE_LIMIT_ENABLED
```

---

# 48. DOCUMENTACIÓN OBLIGATORIA

Cada módulo debe documentar:

- objetivo;
- reglas;
- endpoints;
- permisos;
- modelo;
- validaciones;
- eventos auditados;
- pruebas;
- decisiones técnicas.

Mantener:

```text
docs/
specs/
context/
CHANGELOG.md
```

actualizados.

---

# 49. AGENTS

OpenCode debe utilizar agentes especializados.

## architect

Responsable:

- arquitectura;
- dependencias;
- patrones;
- ADRs.

## backend

Responsable:

- FastAPI;
- servicios;
- repositories;
- API.

## frontend

Responsable:

- UI;
- UX;
- rutas;
- dashboards.

## database

Responsable:

- PostgreSQL;
- migraciones;
- RLS;
- índices.

## security

Responsable:

- threat modeling;
- autenticación;
- autorización;
- MFA;
- hardening.

## qa

Responsable:

- pruebas;
- cobertura;
- regression.

## devops

Responsable:

- Docker;
- Nginx;
- despliegue;
- observabilidad.

## documentation

Responsable:

- README;
- specs;
- documentación técnica;
- CHANGELOG.

---

# 50. ORDEN DE EJECUCIÓN

Ejecutar el proyecto por fases.

## Fase 0 — Auditoría inicial

- inspeccionar proyecto;
- inventariar archivos;
- identificar stack;
- detectar deuda técnica;
- analizar seguridad;
- detectar duplicados;
- revisar migraciones;
- ejecutar tests existentes.

Resultado:

```text
docs/architecture/auditoria_inicial.md
```

---

# 51. FASE 1 — NÚCLEO BASE

Implementar:

- municipios;
- planes de desarrollo;
- dependencias;
- vigencias;
- usuarios;
- roles;
- permisos;
- autenticación;
- auditoría base;
- RLS.

Resultado esperado:

un núcleo seguro y multi-municipio.

---

# 52. FASE 2 — GESTORES LÍDERES

Implementar completamente:

- modelo;
- migración;
- service;
- repository;
- schemas;
- API;
- permisos;
- UI;
- filtros;
- asistente;
- password temporal;
- cambio obligatorio;
- MFA;
- auditoría;
- sesiones;
- bloqueo;
- eliminación lógica;
- pruebas.

No avanzar hasta superar Quality Gate.

---

# 53. FASE 3 — LÍNEAS ESTRATÉGICAS

Implementar:

- CRUD;
- permisos;
- RLS;
- auditoría;
- UI;
- pruebas.

---

# 54. FASE 4 — PROGRAMAS

Implementar:

- CRUD;
- relación línea;
- permisos;
- RLS;
- auditoría;
- UI;
- pruebas.

---

# 55. FASE 5 — PRODUCTOS

Implementar:

- CRUD;
- relación programa;
- gestor responsable;
- dependencia;
- permisos;
- auditoría;
- UI;
- pruebas.

---

# 56. FASE 6 — DASHBOARDS

## Administrador

Crear dashboard consolidado.

## Gestor

Crear dashboard independiente.

No compartir componentes que introduzcan fugas de permisos.

Compartir únicamente componentes visuales seguros y servicios genéricos.

---

# 57. QUALITY GATE

Antes de considerar una fase terminada verificar:

```text
[ ] Compila
[ ] Migraciones funcionan
[ ] Tests pasan
[ ] No hay errores críticos
[ ] No hay secretos en Git
[ ] Validación server-side
[ ] Autorización server-side
[ ] RLS verificado
[ ] Auditoría activa
[ ] UI responsive
[ ] Documentación actualizada
[ ] CHANGELOG actualizado
[ ] No existen TODO críticos
```

No avanzar con fallos críticos.

---

# 58. PROJECT_RULES

Reglas obligatorias:

1. No eliminar código funcional sin analizar dependencias.
2. No cambiar arquitectura silenciosamente.
3. No crear duplicados.
4. No hardcodear secretos.
5. No hardcodear municipios.
6. No hardcodear usuarios.
7. No confiar en frontend para seguridad.
8. No saltarse migraciones.
9. No ejecutar SQL destructivo sin respaldo.
10. No borrar históricos auditables.
11. No guardar passwords.
12. No guardar tokens en logs.
13. No almacenar secretos MFA en texto plano.
14. No reutilizar IDs externos como PK.
15. No dejar endpoints críticos sin permisos.
16. No terminar módulos sin tests.
17. No avanzar de fase con errores críticos.

---

# 59. FORMA DE TRABAJO DE OPENCODE

Antes de cada fase:

1. leer MASTER_PROMPT.md;
2. leer PROJECT_RULES.md;
3. leer ROADMAP.md;
4. leer specs correspondientes;
5. inspeccionar código existente;
6. presentar plan de cambios;
7. identificar archivos afectados;
8. identificar migraciones necesarias;
9. implementar;
10. ejecutar pruebas;
11. corregir errores;
12. actualizar documentación;
13. actualizar CHANGELOG.

---

# 60. RESTRICCIÓN DE CAMBIOS

Cuando detectes una mejora:

- no implementarla automáticamente si cambia el alcance;
- documentarla en:

```text
context/decisions.md
```

o crear ADR.

Clasificar:

```text
CRÍTICA
RECOMENDADA
OPCIONAL
FUTURA
```

Las mejoras críticas de seguridad sí deben bloquear la fase hasta resolución.

---

# 61. ROADMAP INICIAL

```text
V1.0
│
├── Núcleo Multi-Municipio
├── Seguridad
├── Usuarios
├── Roles
├── Permisos
├── Gestores Líderes
├── Líneas Estratégicas
├── Programas
└── Productos

V1.1
│
├── Metas
├── Indicadores
├── Avances
└── Evidencias

V1.2
│
├── Dashboards avanzados
├── Alertas
├── Semáforos
├── Consolidación
└── Reportes

V2
│
├── Informe de Gestión
├── Rendición de Cuentas
├── Analítica avanzada
├── Integraciones
└── Firma / validación avanzada
```

---

# 62. PRIMERA TAREA DE OPENCODE

Cuando se entregue este archivo a OpenCode, ejecutar primero:

```text
Lee completamente:

README.md
MASTER_PROMPT.md
AGENTS.md
PROJECT_RULES.md
ROADMAP.md
context/
specs/
migrations/

Después:

1. Audita el proyecto actual.
2. Identifica qué existe y qué falta.
3. No modifiques código todavía hasta terminar el inventario.
4. Genera docs/architecture/auditoria_inicial.md.
5. Genera una matriz:
   - requisito,
   - existente,
   - parcial,
   - faltante,
   - riesgo,
   - recomendación,
   - archivos afectados.
6. Define el orden exacto de implementación del Núcleo Central V1.
7. Comienza Fase 1 únicamente después de dejar documentado el estado inicial.
```

---

# 63. PRIMER OBJETIVO FUNCIONAL

El primer objetivo operativo será:

> Construir completamente el módulo Gestores Líderes sobre una base multi-municipio segura, implementando autenticación, roles, permisos, RLS, generación de contraseña temporal, cambio obligatorio, MFA, sesiones, intentos fallidos, bloqueo, auditoría y separación absoluta entre Dashboard Administrador y Dashboard Gestor.

Ese módulo se convierte en patrón de arquitectura para el resto de SIGEM.

---

# 64. CRITERIO DE ÉXITO

SIGEM V1 se considerará correctamente construido cuando:

- un municipio tenga aislamiento real;
- un Administrador gestione sus Gestores;
- un Gestor no pueda acceder a recursos ajenos;
- la separación exista en frontend, backend y BD;
- todas las acciones críticas sean auditables;
- contraseñas nunca se almacenen en texto plano;
- MFA funcione;
- RLS esté probado;
- Línea → Programa → Producto esté correctamente relacionada;
- los dashboards sean independientes;
- el sistema pueda consolidar datos sin romper aislamiento;
- las pruebas automatizadas validen los flujos críticos.

---

# 65. REGLA FINAL

No optimices prematuramente.

No construyas funcionalidades fuera del alcance antes de asegurar el núcleo.

Primero:

```text
SEGURIDAD
↓
USUARIOS
↓
PERMISOS
↓
GESTORES
↓
ESTRUCTURA PLAN DE DESARROLLO
↓
PRODUCTOS
↓
METAS
↓
INDICADORES
↓
EVIDENCIAS
↓
REPORTES
```

SIGEM Colombia debe crecer sobre un núcleo:

**robusto, trazable, seguro, mantenible, auditable y escalable.**
