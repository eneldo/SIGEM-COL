# Decisiones Técnicas

## 2026-09-21 - Acciones inline estándar en todas las tablas CRUD

Se reemplazaron los menús portales de三点 (dots) por botones inline de acción en Líneas, Programas y Productos, siguiendo el patrón ya establecido en Gestores. Cada tabla ahora muestra directamente los botones de acción relevantes para su módulo:
- **Gestores**: Editar, Eliminar, Ver detalles, Activar/Desactivar, Permisos, Cambiar contraseña.
- **Líneas estratégicas**: Editar, Eliminar.
- **Programas**: Editar, Eliminar.
- **Productos**: Editar, Eliminar.

Se eliminaron `createPortal`, `useRef` y el estado `menu` de las tres páginas. El componente `ActionButton` es idéntico en todas: `h-8 w-8 rounded-lg border`, variante `danger` para eliminar.

## 2026-09-20 - Contratos frontend alineados con backend

Los identificadores de líneas, programas y productos se manejan como UUID en formato `string`. Se eliminaron del frontend los campos inexistentes `color`, `activa`, `avance_porcentaje`, `meta` y fechas operativas de producto. Los estados se consumen desde el campo `estado` del backend.

## 2026-09-20 - Respuestas API sin envoltorio artificial

Los endpoints CRUD de líneas, programas y productos y los endpoints de dashboard se tipan según su respuesta directa de FastAPI. No se usa `ApiResponse<T>` donde el servidor retorna directamente el recurso o colección.

## 2026-09-20 - Nombre del plan en LineaResponse

Se agregó `plan_desarrollo_nombre` opcional a `LineaResponse`. El servicio ya generaba este valor, pero Pydantic lo descartaba al no estar definido en el schema.

## 2026-09-20 - Persistencia de autenticación ante 401

Ante un 401 fuera del endpoint de login se eliminan `token`, `user` y `sigem-auth`, se evita más de una redirección simultánea y se reemplaza la ubicación por `/login`. Esto previene el ciclo entre login y dashboard causado por estado persistido inconsistente.

## 2026-09-20 - Fix datetime en servicios backend

Los servicios `linea_service.py`, `programa_service.py` y `producto_service.py` usaban `datetime.now(timezone.utc)` (timezone-aware), pero las columnas DB son `TIMESTAMP WITHOUT TIME ZONE`. Se cambió a `datetime.utcnow()` (naive) para evitar errores 500 al crear registros.
