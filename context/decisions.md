# Decisiones Técnicas

## 2026-09-22 - Suite de tests completa (76 tests pasando)

Se creó la suite de tests completa contra el backend Docker en vivo (`localhost:8001`). Tests de autenticación, CRUD, RBAC, integración y seguridad. Fixtures en `conftest.py` con tokens de admin, gestor y superadmin. Rate limit ajustado a 2000 req/15min para evitar 429 durante ejecución de tests.

## 2026-09-22 - Docker deployment completo

Docker Compose con 4 servicios: backend (FastAPI), frontend (nginx+React), PostgreSQL 17, Redis 7. Backend en puerto 8001, frontend en 3001, PG en 5433 (local PG ocupa 5432). Secretos via `.env` + `env_file`. Health checks en todos los servicios. Contenedor backend como non-root (`USER app`).

## 2026-09-22 - RLS (Row-Level Security) activado

`RLSMiddleware` extrae `municipio_id` del JWT y lo almacena en `request.state`. `get_db_with_rls` ejecuta `set_config('app.current_municipio_id', municipio_id)` antes de cada query. Todas las tablas multi-municipio tienen policies RLS `municipio_isolation_*`. Auth modificado para usar `get_db_with_rls` en lugar de `get_db`.

## 2026-09-22 - RBAC real en dashboards

Reemplazado placeholder `# TODO: Verificar permisos` por `await require_permission(db, user.id, permission)` en `dashboard/admin.py` y `dashboard/gestor.py`. Permisos: `dashboard.admin.ver`, `dashboard.gestor.ver`.

## 2026-09-22 - Seed de usuarios en Docker DB

Creados 9 usuarios en Docker PostgreSQL via script inline: admin (SUPERADMIN_PLATAFORMA), superadmin (SUPERADMIN_PLATAFORMA), 7 gestores (GESTOR_LIDER). Municipio default `00000` (`bdb39d8c`). Gestores con passwords documentados.

## 2026-09-22 - migrations/env.pylee DATABASE_URL de env var

Para que Alembic funcione tanto local como en Docker, `migrations/env.py` verifica `os.environ.get("DATABASE_URL")` y sobreescribe `sqlalchemy.url` si existe. Ejecución en Docker: `docker exec --env DATABASE_URL=... sigem-backend python -m alembic upgrade head`.

## 2026-09-21 - Acciones inline estándar en todas las tablas CRUD

Se reemplazaron los menús portales por botones inline de acción en Líneas, Programas y Productos, siguiendo el patrón de Gestores. Cada tabla muestra directamente los botones de acción. Se eliminaron `createPortal`, `useRef` y estado `menu`. Componente `ActionButton` reutilizable: `h-8 w-8 rounded-lg border`.

## 2026-09-21 - Password change modal sin redirect forzado

Se eliminó el redirect forzado a `/change-password` en `App.tsx`. Nuevo `PasswordChangeModal`: aparece después de 5min (cancelable), obligatorio a 10min (no se puede cerrar). Usa `loginTimestamp`, `passwordChangeDismissed`, `dismissPasswordChange()` en authStore.

## 2026-09-20 - Contratos frontend alineados con backend

Los identificadores se manejan como UUID en formato `string`. Se eliminaron campos inexistentes. Los estados se consumen desde el campo `estado` del backend.

## 2026-09-20 - Respuestas API sin envoltorio artificial

No se usa `ApiResponse<T>` donde el servidor retorna directamente el recurso o colección.

## 2026-09-20 - Persistencia de autenticación ante 401

Ante un 401 fuera del login se eliminan `token`, `user` y `sigem-auth`, se evita más de una redirección simultánea y se reemplaza ubicación por `/login`.

## 2026-09-20 - Fix datetime en servicios backend

Los servicios usaban `datetime.now(timezone.utc)` (timezone-aware) pero las columnas DB son `TIMESTAMP WITHOUT TIME ZONE`. Se cambió a `datetime.utcnow()` (naive).

## 2026-09-20 - Selector de accent color

Se implementó selector de color de acento (azul, verde, ámbar, púrpura, rosa) en Configuración con preview en vivo y persistencia en `localStorage`.

## Convenciones importantes

- `get_current_user_from_token` retorna `{user, municipio_id, roles, permissions}`. Acceder a roles via `current_user["roles"]`, NO `user.roles`.
- Python venv: `src/backend/.venv/`. Ejecutar con `F:\SIGEM-COL\src\backend\.venv\Scripts\python.exe`.
- Frontend no soporta alias `@/*` — usar imports relativos en componentes.
- Backend arranque: `cd F:\SIGEM-COL && src\backend\.venv\Scripts\python.exe -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload`.
- Frontend arranque: `cd F:\SIGEM-COL\src\frontend && npm run dev`.
- Tests ejecutar: `cd F:\SIGEM-COL && src\backend\.venv\Scripts\python.exe -m pytest tests/ -v`.
