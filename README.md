# SIGEM Colombia

**Sistema de Información para el Seguimiento al Plan de Desarrollo Municipal**

---

## Descripción

SIGEM Colombia es un sistema institucional diseñado para el seguimiento, medición, control de cumplimiento y generación de informes sobre las metas del Plan de Desarrollo Municipal.

### Características Principales

- **Multi-municipio:** Soporte para múltiples municipios con aislamiento seguro de información
- **Seguridad robusta:** RBAC, ABAC, PostgreSQL RLS, MFA, auditoría completa
- **Arquitectura modular:** Monolito modular desacoplado, preparado para futura separación
- **API-first:** Todas las funcionalidades expuestas vía REST API
- **Dashboard separados:** Vistas independientes para Administrador y Gestor

---

## Stack Tecnológico

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL 17+
- Redis
- JWT + Argon2id
- MFA (WebAuthn/TOTP)

### Frontend
- React
- TypeScript
- Vite

### Infraestructura
- Docker
- Docker Compose
- Nginx
- PostgreSQL
- Redis

---

## Estructura del Proyecto

```
SIGEM_COLOMBIA/
├── .github/             # Pipelines de GitHub Actions
├── agents/              # Agentes especializados
├── context/             # Contexto del proyecto
├── orchestration/       # Orquestación de workflows
├── roles/               # Definición de roles
├── specs/               # Especificaciones por módulo
├── docs/                # Documentación técnica y runbooks
├── src/
│   ├── backend/         # Código Python/FastAPI
│   └── frontend/        # Código React/TypeScript
├── tests/               # Pruebas automatizadas
├── migrations/          # Migraciones Alembic
├── scripts/             # Scripts de soporte
├── infra/               # Infraestructura Docker, nginx y TLS
└── security/            # Seguridad y hardening
```

---

## Inicio Rápido

### Prerrequisitos

- Docker y Docker Compose
- Python 3.12+
- Node.js 20+

### Instalación

1. Clonar el repositorio:
```bash
git clone <url-repositorio>
cd SIGEM_COLOMBIA
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con valores de desarrollo
```

3. Levantar servicios:
```bash
docker compose -f infra/docker/docker-compose.yml up -d --build
```

4. Ejecutar migraciones:
```bash
docker compose -f infra/docker/docker-compose.yml exec backend alembic upgrade head
```

5. Acceder a la aplicación (puertos de desarrollo):
- Frontend: http://localhost:3001
- Backend API: http://localhost:8001/docs
- PostgreSQL: localhost:5433 (usuario `sigem`)

### Endpoints operativos del backend

| Endpoint | Descripción |
|---|---|
| `GET /health` | salud agregada: `200` healthy / `503` degraded (depende de la base de datos) |
| `GET /health/live` | proceso vivo (liveness) |
| `GET /health/ready` | readiness: listo para recibir tráfico |
| `GET /metrics` | métricas Prometheus; si `METRICS_TOKEN` está definido requiere `Authorization: Bearer <token>` |

---

## Documentación

- [Auditoría Inicial](docs/architecture/auditoria_inicial.md)
- [Matriz de Requisitos](docs/architecture/matriz_requisitos.md)
- [Orden de Implementación V1](docs/architecture/orden_implementacion_v1.md)
- [CI/CD](docs/operations/ci-cd.md)
- [MASTER_PROMPT](MASTER_PROMPT_SIGEM_COLOMBIA_V1.md)

---

## Producción

El stack productivo usa `infra/docker/docker-compose.prod.yml` (proyecto `sigem-prod`) y expone **solo nginx en 80/443 con TLS**:

```bash
bash scripts/setup/deploy.sh <tag>
```

Runbooks de operación (leer antes de tocar producción):

- [Despliegue y rollback](docs/operations/deployment.md) — topología, primer despliegue, checklist, job `deploy` de CI/CD y secretos
- [TLS](docs/operations/tls.md) — certificados en `infra/tls/` y `nginx.prod.conf`
- [Backups](docs/operations/backups.md) — dump de BD + evidencias, retención y verificación
- [Monitoreo](docs/operations/monitoring.md) — perfil `monitoring`, Prometheus y alertas
- [CI/CD](docs/operations/ci-cd.md) — pipeline, gates, umbrales y secretos de GitHub

---

## Desarrollo

### Reglas del Proyecto

Ver [PROJECT_RULES.md](PROJECT_RULES.md) para reglas obligatorias.

### Agentes IA

Ver [AGENTS.md](AGENTS.md) para definición de agentes especializados.

### Roadmap

Ver [ROADMAP.md](ROADMAP.md) para hoja de ruta completa.

---

## Seguridad

- Nunca almacenar secretos en código
- Usar variables de entorno
- MFA obligatorio para Administradores
- Contraseñas con Argon2id
- Auditoría completa de acciones
- RLS en todas las tablas multi-municipio

Reportar vulnerabilidades a: [correo de seguridad]

---

## Licencia

[Determinar licencia]

---

**Versión actual:** V1.0 (En desarrollo)
