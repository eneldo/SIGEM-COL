# CI/CD — GitHub Actions

**Pipeline:** `.github/workflows/ci.yml`
**Alcance:** calidad (backend y frontend), seguridad, construcción de imágenes y despliegue manual a producción.
**Principio:** ningún job tiene `continue-on-error`; todo gate falla el pipeline.

---

## 1. Disparadores

| Evento | Condición | Jobs que corren |
|---|---|---|
| `push` a `master` | siempre | backend-quality, backend-tests, frontend-quality, security, docker-build |
| `pull_request` a `master` | siempre | backend-quality, backend-tests, frontend-quality, security, docker-build |
| `workflow_dispatch` | requiere el input `deploy_tag` | todos, **+ deploy** |

El job `deploy` tiene `if: github.event_name == 'workflow_dispatch'`, por lo que **un push jamás despliega**. En `push`/`pull_request` aparece como *skipped*.

---

## 2. Jobs

| Job | Runner | Contenido |
|---|---|---|
| `backend-quality` | ubuntu-latest, Python 3.12 | `pip install -e ".[dev]"` en `src/backend`, luego `ruff check`, `ruff format --check`, `mypy`, `bandit` desde la raíz del repo |
| `backend-tests` | ubuntu-latest, Python 3.12 | servicios `postgres:17` y `redis:7` con health checks; instala el paquete y ejecuta pytest con cobertura |
| `frontend-quality` | ubuntu-latest, Node 20, `working-directory: src/frontend` | `npm ci` → `npx tsc --noEmit` → `npm run lint` → `npm run test:coverage` → `npm run build` |
| `security` | ubuntu-latest | (a) gitleaks, (b) pip-audit, (c) `npm audit` de dependencias de producción |
| `docker-build` | ubuntu-latest | construye `infra/docker/backend/Dockerfile` e `infra/docker/frontend/Dockerfile` con contexto en la raíz, etiquetas `sigem-backend:sha-<commit>` / `sigem-frontend:sha-<commit>`, **sin push**, caché GHA (`type=gha`) |
| `deploy` | ubuntu-latest | solo `workflow_dispatch`; valida secretos y ejecuta `scripts/setup/deploy.sh <tag>` por SSH en el host de producción |

Dependencias: `deploy` → `needs: [backend-quality, backend-tests, frontend-quality, security]`.

### Comando único de pruebas backend

La invocación canónica de pytest está definida **una sola vez** como variable de entorno de nivel workflow:

```yaml
env:
  PYTEST_CMD: python -m pytest tests -c src/backend/pyproject.toml --cov-report=xml --cov-fail-under=80
```

Si el equipo de QA ajusta la invocación canónica (markers, `-n`, ruta de config), se cambia **esa línea** y nada más.

---

## 3. Gates y umbrales

### Backend

| Gate | Comando | Umbral |
|---|---|---|
| Lint | `python -m ruff check src/backend tests` | cero errores |
| Formato | `python -m ruff format --check src/backend tests` | cero archivos desordenados |
| Tipos | `python -m mypy src/backend` | strict, cero errores |
| Seguridad estática | `python -m bandit -r src/backend -ll` | cero hallazgos nivel ≥ medium |
| Pruebas + cobertura | `PYTEST_CMD` | todo verde y **cobertura global ≥ 80 %** (`--cov-fail-under=80`; pytest-cov falla si no se cumple) |

La variable `PYTEST_CMD` también emite `coverage.xml` en la raíz, que se publica como resumen del job y como artefacto `backend-coverage`.

> **Nota de integración:** el gate del 80 % se aplica hoy desde `PYTEST_CMD`. Cuando `[tool.coverage.report] fail_under` quede fijado en `src/backend/pyproject.toml`, se puede retirar `--cov-fail-under=80` del workflow sin perder la restricción.

### Frontend

| Gate | Comando | Umbral |
|---|---|---|
| Tipos | `npx tsc --noEmit` | cero errores |
| Lint | `npm run lint` (`--max-warnings 0`) | cero errores **y cero warnings** |
| Cobertura | `npm run test:coverage` | umbrales de `src/frontend/vite.config.ts`: líneas 17 %, statements 17 %, ramas 90 %, funciones 85 %, más umbrales por archivo (80 %) en `EvidencePreview`, `EvidenciasModal`, `components/ui/*`, `lib/api.ts`, `stores/authStore.ts`, `pages/auth/LoginPage`, `pages/auth/ChangePasswordPage` |
| Build | `npm run build` (`tsc && vite build`) | cero errores |

Artefacto: `frontend-coverage` (directorio `src/frontend/coverage`, reportes `text` + `lcov`).

### Seguridad

| Gate | Herramienta | Comportamiento |
|---|---|---|
| Secretos | `gitleaks/gitleaks-action@v3` con `GITLEAKS_CONFIG=.gitleaks.toml`, `fetch-depth: 0` | escanea historial completo; falla ante cualquier hallazgo no allowlisteado |
| Dependencias Python | `python -m pip_audit` tras `pip install -e ".[dev]"` | falla ante cualquier CVE no ignorado |
| Dependencias Node | `npm audit --omit=dev --audit-level=high` en `src/frontend` | falla ante CVE de severidad **high** o **critical** en dependencias de producción |

---

## 4. Cobertura

### Backend — 80 %

Gate duro: `--cov-fail-under=80` sobre `--cov=src/backend` (configuración `[tool.pytest.ini_options]` / `[tool.coverage.*]` de `src/backend/pyproject.toml`). El job falla si no se cumple; `coverage.xml` se sube como artefacto y se imprime en el *job summary*.

### Frontend — rampa de cobertura

Umbrales vigentes (globales): **líneas 17 %, statements 17 %, ramas 90 %, funciones 85 %**.

**RAMP — áreas todavía sin cubrir** (candidatas a subir umbrales cuando se les agreguen tests):

| Área | Archivos | Estado |
|---|---|---|
| `src/pages/admin/` | 13 archivos (`AuditoriaPage`, `ConfiguracionPage`, `CumplimientoPage`, `DashboardAdmin`, `DependenciasPage`, `GestoresPage`, `LineasPage`, `PersonalizacionPage`, `ProductosPage`, `ProgramasPage`, `ReportesPage`, `RolesPage`, `UsuariosPage`) | 0 % líneas |
| `src/pages/gestor/` | 7 archivos (`DashboardGestor`, `GestorAsignarPage`, `GestorDashboardPage`, `GestorEquipoPage`, `MisProductosPage`, `RegistroAvancePage`, `RevisionAvancesPage`) | 0 % líneas |
| `src/components/layout/` | `Header.tsx`, `Layout.tsx`, `Sidebar.tsx` | 0 % líneas |
| `src/components/` | `PasswordChangeModal.tsx`, `TimelineAvance.tsx` | 0 % líneas |
| `src/App.tsx` | rutas y guardas de navegación | 0 % líneas |

Al cubrir estos archivos se debe **subir** `lines`/`statements` en `vite.config.ts`; en ningún caso bajarlos.

---

## 5. Secretos de GitHub requeridos

Configurar en **Settings → Secrets and variables → Actions** del repositorio:

| Secreto | Propósito | Cómo generarlo |
|---|---|---|
| `DEPLOY_HOST` | Hostname o IP del servidor de producción | dominio o IP pública del servidor (valor literal) |
| `DEPLOY_USER` | Usuario SSH con el que ejecuta el despliegue | usuario del servidor (p. ej. `deploy`); debe tener permiso para `docker compose` en `DEPLOY_PATH` |
| `DEPLOY_PATH` | Ruta absoluta del clon del repo en el servidor | p. ej. `/srv/sigem-col` (valor literal) |
| `SSH_PRIVATE_KEY` | Clave privada SSH sin passphrase usada por `appleboy/ssh-action` | `ssh-keygen -t ed25519 -C "github-actions-deploy"`; la **clave pública** se copia al `~/.ssh/authorized_keys` del `DEPLOY_USER`. Guardar la clave completa, incluyendo `-----BEGIN ...-----` y `-----END ...-----` |
| `GITHUB_TOKEN` | Proporcionado automáticamente por GitHub | no se configura a mano; lo inyecta la plataforma (lo usa gitleaks para comentar en PRs) |

Si alguno de los cuatro secretos de despliegue falta, el job `deploy` **falla con un mensaje explícito** (`Missing required GitHub secrets: ...`) en lugar de omitir el despliegue en silencio.

Comprobación local del flujo de despliegue (equivalente manual): ver `docs/operations/deployment.md`.

---

## 6. Resultados (hallazgos conocidos)

### gitleaks — allowlist (`.gitleaks.toml`)

Escaneos locales ejecutados (historial con `detect` y árbol de trabajo con `detect --no-git`):

| Placeholder allowlisteado | Dónde vive | Motivo |
|---|---|---|
| `manything_12345` | `tests/security/test_security.py` (commit histórico) | clave de fixture de prueba; no abre ningún sistema |
| `anything_12345` | `tests/security/test_security.py` (versión actual) | clave de fixture de prueba; no abre ningún sistema |

La allowlist usa `regexes` con esos valores exactos (más `[extend] useDefault = true` para conservar el reglamento por defecto). **Si el fixture de contraseña de `tests/security/test_security.py` cambia de valor, hay que agregar el nuevo literal aquí**; nunca se allowlistea `.env`, claves TLS ni ningún secreto real.

Verificación de que el reglamento sigue activo: una clave sintética insertada en una copia del árbol sí es detectada (el allowlist no desactiva el escaneo).

### pip-audit — CVEs ignorados

Ejecución local en un venv limpio con solo `pip install -e "src/backend[dev]"` (equivalente al job de CI):

```
ecdsa 0.19.2  PYSEC-2026-1325  (sin versión de fix)
nltk  3.10.3  PYSEC-2026-3740  (sin versión de fix)
```

| ID ignorado | Paquete | Origen | Justificación |
|---|---|---|---|
| `PYSEC-2026-1325` | `ecdsa 0.19.2` | dependencia de `python-jose` | el advisory no publica versión corregida; no hay acción posible en el consumidor |
| `PYSEC-2026-3740` | `nltk 3.10.3` | dependencia de `safety` (extra `dev`) | el advisory no publica versión corregida; dependencia de una herramienta de desarrollo, no del runtime |

Banderas usadas: `--ignore-vuln PYSEC-2026-1325 --ignore-vuln PYSEC-2026-3740`. Con ellas, `pip_audit` sale con 0. **Cualquier nuevo CVE falla el job** hasta que se revise y, si corresponde, se documente aquí.

### npm audit — dependencias de producción

`npm audit --omit=dev --audit-level=high` en `src/frontend`: **0 high/critical** (pasa). Quedan 2 advisories *moderate* en `react-router`/`react-router-dom` 6.x (GHSA-wrjc-x8rr-h8h6 y GHSA-337j-9hxr-rhxg); la corrección obliga a `react-router-dom@7`, cambio mayor que debe planificarse por separado. El umbral `--audit-level=high` no se relaja: si aparece un high/critical, el job falla.

---

## 7. Cada gate en local

### Backend

```bash
python -m pip install -e "src/backend[dev]"

python -m ruff check src/backend tests
python -m ruff format --check src/backend tests
python -m mypy src/backend
python -m bandit -r src/backend -ll

export DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test"
export REDIS_URL="redis://localhost:6379/0"
export RATE_LIMIT_LOGIN_ATTEMPTS=10000000
export RATE_LIMIT_DEFAULT_REQUESTS=10000000
python -m pytest tests -c src/backend/pyproject.toml --cov-report=xml --cov-fail-under=80
```

### Frontend

```bash
cd src/frontend
npm ci
npx tsc --noEmit
npm run lint
npm run test:coverage
npm run build
```

### Seguridad

```bash
docker run --rm -v "${PWD}:/repo" -w /repo zricethezav/gitleaks:latest detect -v

python -m pip install pip-audit
python -m pip_audit --ignore-vuln PYSEC-2026-1325 --ignore-vuln PYSEC-2026-3740

cd src/frontend
npm audit --omit=dev --audit-level=high
```

### Imágenes Docker

```bash
docker build -f infra/docker/backend/Dockerfile -t sigem-backend:sha-local .
docker build -f infra/docker/frontend/Dockerfile -t sigem-frontend:sha-local .
```

### Validación del workflow

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
docker run --rm -v "${PWD}:/repo" -w /repo rhysd/actionlint:latest .github/workflows/ci.yml
```

---

## 8. Notas de integración

1. **`PYTEST_CMD` es la suposición de trabajo** (`python -m pytest tests -c src/backend/pyproject.toml ...`). Si el equipo de QA define otra invocación canónica, se edita exclusivamente esa variable de entorno.
2. El job `backend-tests` **no aplica migraciones ni levanta la API**: si la suite canónica necesita esquema o un servidor vivo, agregar un paso de preparación (p. ej. `python -m alembic upgrade head` con `ALEMBIC_DATABASE_URL`, o un servicio `uvicorn`) antes del paso de pytest.
3. `gitleaks-action` se fija en `@v3`: `@v2` ejecuta Node 20 y dejó de ser soportado en GitHub runners desde el 2026-09-16 (ver el README de `gitleaks/gitleaks-action`).
4. `npm audit` usa `--omit=dev`; `--production` es el alias obsoleto del mismo flag.
