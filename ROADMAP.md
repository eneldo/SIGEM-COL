# ROADMAP — SIGEM Colombia

**Fecha:** 2026-09-20  
**Versión:** 1.0  
**Objetivo:** Hoja de ruta completa del proyecto SIGEM Colombia.

---

## Visión General

SIGEM Colombia se desarrollará en **4 versiones principales**, cada una con objetivos claros y dependencias definidas.

---

## V1.0 — Núcleo Central

**Estado:** En desarrollo  
**Objetivo:** Sistema multi-municipio completo con seguridad y módulos base.

### Fase 0 — Configuración Inicial
- [ ] Inicializar repositorio Git
- [ ] Configurar Docker Compose
- [ ] Crear estructura FastAPI
- [ ] Crear estructura React
- [ ] Configurar Alembic
- [ ] Verificar entorno funcional

### Fase 1 — Núcleo Base (Seguridad)
- [ ] Modelos: municipios, planes, vigencias, dependencias
- [ ] Modelos: usuarios, roles, permisos
- [ ] Migración inicial
- [ ] Configurar RLS
- [ ] Autenticación JWT
- [ ] Hashing Argon2id
- [ ] MFA (TOTP)
- [ ] Rate limiting
- [ ] Auditoría base
- [ ] Tests de seguridad

### Fase 2 — Gestores Líderes
- [ ] Modelo gestores_lideres
- [ ] CRUD completo
- [ ] Asistente por pasos (4 pasos)
- [ ] Generación código legible (GES-XXXXXX)
- [ ] Username automático
- [ ] Contraseña temporal segura
- [ ] Cambio obligatorio
- [ ] Permisos granulares
- [ ] Auditoría de gestores
- [ ] UI completa
- [ ] Tests E2E

### Fase 3 — Líneas Estratégicas
- [ ] Modelo lineas_estrategicas
- [ ] CRUD completo
- [ ] Validación código único por plan
- [ ] RLS
- [ ] UI
- [ ] Tests

### Fase 4 — Programas
- [ ] Modelo programas
- [ ] CRUD completo
- [ ] Relación línea-programa
- [ ] RLS
- [ ] UI
- [ ] Tests

### Fase 5 — Productos
- [ ] Modelo productos
- [ ] CRUD completo
- [ ] Asignación gestor responsable
- [ ] Asignación dependencia
- [ ] RLS
- [ ] UI
- [ ] Tests
- [ ] Preparado para metas/indicadores

### Fase 6 — Dashboards
- [ ] Dashboard Administrador consolidado
- [ ] Dashboard Gestor independiente
- [ ] KPIs por rol
- [ ] Consolidación sin romper aislamiento
- [ ] UI responsive
- [ ] Tests de aislamiento

### Criterios de Éxito V1.0
- [ ] Multi-municipio funcional
- [ ] Aislamiento real verificado
- [ ] Gestores gestionables por Admin
- [ ] Gestor no accede a recursos ajenos
- [ ] Separación en frontend, backend y BD
- [ ] Acciones críticas auditables
- [ ] Contraseñas nunca en texto plano
- [ ] MFA funcional
- [ ] RLS probado
- [ ] Línea → Programa → Producto relacionado
- [ ] Dashboards independientes
- [ ] Consolidación funciona
- [ ] Tests automatizados pasan

---

## V1.1 — Metas e Indicadores

**Estado:** Pendiente  
**Objetivo:** Implementar seguimiento a avances y medición de cumplimiento.

### Módulos
- [ ] Metas
  - [ ] Modelo metas
  - [ ] CRUD completo
  - [ ] Relación producto-meta
  - [ ] Tipos de meta (cuantitativa/cualitativa)
  - [ ] Periodo de medición
  - [ ] UI

- [ ] Indicadores
  - [ ] Modelo indicadores
  - [ ] CRUD completo
  - [ ] Fórmulas de cálculo
  - [ ] Fuentes de datos
  - [ ] Meta/real
  - [ ] UI

- [ ] Avances
  - [ ] Modelo avances
  - [ ] Registro de avances
  - [ ] Validación contra metas
  - [ ] Estados (pendiente, en proceso, completado)
  - [ ] UI

- [ ] Evidencias
  - [ ] Modelo evidencias
  - [ ] Carga de archivos
  - [ ] Versionado
  - [ ] Validación MIME/bytes
  - [ ] Hash SHA-256
  - [ ] Auditoría de carga
  - [ ] UI

### Criterios de Éxito V1.1
- [ ] Metas registradas por producto
- [ ] Indicadores calculados automáticamente
- [ ] Avances registrados y validados
- [ ] Evidencias almacenadas de forma segura
- [ ] Dashboard Admin muestra consolidación
- [ ] Dashboard Gestor muestra sus avances

---

## V1.2 — Dashboards Avanzados

**Estado:** Pendiente  
**Objetivo:** Visualización avanzada y reportes.

### Módulos
- [ ] Dashboards avanzados
  - [ ] Gráficos de tendencia
  - [ ] Comparativos
  - [ ] Filtros avanzados
  - [ ] Exportación

- [ ] Alertas
  - [ ] Configuración de alertas
  - [ ] Notificaciones
  - [ ] Umbral personalizable

- [ ] Semáforos
  - [ ] Estados visuales
  - [ ] Reglas de negocio
  - [ ] Dashboard semáforo

- [ ] Consolidación
  - [ ] Agregación por nivel
  - [ ] Cross-municipio (para SuperAdmin)
  - [ ] Exportación datos

- [ ] Reportes
  - [ ] Generación PDF
  - [ ] Reportes personalizados
  - [ ] Programación de reportes

### Criterios de Éxito V1.2
- [ ] Dashboards con gráficos funcionales
- [ ] Alertas configurables
- [ ] Semáforos visuales
- [ ] Consolidación multi-nivel
- [ ] Reportes exportables

---

## V2 — Funcionalidades Avanzadas

**Estado:** Futuro  
**Objetivo:** Funcionalidades institucionales avanzadas.

### Módulos
- [ ] Informe de Gestión
  - [ ] Generación automática
  - [ ] Formato oficial
  - [ ] Aprobación digital

- [ ] Rendición de Cuentas
  - [ ] Generación de informes
  - [ ] Transparencia pública
  - [ ] Datos abiertos

- [ ] Analítica Avanzada
  - [ ] Predicciones
  - [ ] Tendencias
  - [ ] Comparativos históricos

- [ ] Integraciones
  - [ ] SISIP
  - [ ] SGP
  - [ ] Otros sistemas municipales

- [ ] Firma/Validación Avanzada
  - [ ] Firma digital
  - [ ] Validación jurídica
  - [ ] Certificados

---

## Dependencias entre Versiones

```
V1.0 (Núcleo)
    ↓
V1.1 (Metas/Indicadores)
    ↓
V1.2 (Dashboards Avanzados)
    ↓
V2 (Funcionalidades Avanzadas)
```

---

## Timeline Estimada

| Versión | Duración Estimada | Objetivo |
|---------|-------------------|----------|
| V1.0 | 6-8 semanas | Núcleo funcional |
| V1.1 | 3-4 semanas | Seguimiento a avances |
| V1.2 | 3-4 semanas | Visualización avanzada |
| V2 | 6-8 semanas | Funcionalidades institucionales |
| **Total** | **18-24 semanas** | **Sistema completo** |

---

## Prioridades

### Crítico (V1.0)
1. Seguridad completa
2. Multi-municipio
3. Gestores Líderes
4. Estructura Plan de Desarrollo
5. Dashboards básicos

### Alto (V1.1)
1. Metas
2. Indicadores
3. Avances
4. Evidencias

### Medio (V1.2)
1. Dashboards avanzados
2. Alertas
3. Semáforos
4. Reportes

### Futuro (V2)
1. Informe de Gestión
2. Integraciones
3. Analítica avanzada

---

##里程碑 (Milestones)

| Hito | Versión | Fecha Objetivo | Estado |
|------|---------|----------------|--------|
| Entorno funcional | V1.0 Fase 0 | Semana 1 | Pendiente |
| Núcleo seguridad | V1.0 Fase 1 | Semana 3 | Pendiente |
| Gestores funcionales | V1.0 Fase 2 | Semana 5 | Pendiente |
| Estructura Plan completa | V1.0 Fase 5 | Semana 7 | Pendiente |
| Dashboards V1 | V1.0 Fase 6 | Semana 8 | Pendiente |
| Metas/Indicadores | V1.1 | Semana 12 | Pendiente |
| Dashboards avanzados | V1.2 | Semana 16 | Pendiente |
| Sistema completo | V2 | Semana 24 | Pendiente |

---

## Notas

- Este roadmap es una guía, no un contrato
- Las fechas son estimadas y pueden variar
- Priorizar calidad sobre velocidad
- No saltarse fases
- Documentar todas las decisiones

---

**Documento generado como parte de la auditoría inicial — Sección 62 del MASTER_PROMPT**
