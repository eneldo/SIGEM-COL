# Contexto del Proyecto SIGEM Colombia

## Estado al 2026-09-21

El núcleo administrativo dispone de autenticación, dashboard, gestión de gestores líderes, líneas estratégicas, programas y productos. El frontend usa React, TypeScript y Vite; el backend usa FastAPI, SQLAlchemy y PostgreSQL.

## Trabajo completado

- Módulo de gestores: CRUD, estados, permisos, dependencias, credenciales temporales, auditoría de accesos y eliminación lógica.
- Dashboard administrativo con KPIs y alertas de seguridad.
- Layout responsive con contenido de ancho completo y navegación lateral controlable en escritorio y móvil.
- Interceptor 401 corregido para limpiar `token`, `user` y `sigem-auth` sin producir ciclos de redirección.
- Contratos frontend de líneas, programas y productos alineados con UUID y campos reales del backend.
- `LineaResponse` incluye `plan_desarrollo_nombre` opcional.
- Backend: `datetime.now(timezone.utc)` → `datetime.utcnow()` en servicios de líneas, programas y productos para evitar 500 con columnas `TIMESTAMP WITHOUT TIME ZONE`.
- Páginas administrativas de líneas, programas y productos rediseñadas al estilo institucional con botones inline de acciones (Editar + Eliminar), sin menús portales.
- Dashboard del gestor alineado con las respuestas reales del backend.
- Ruta `/gestor/productos` y página de productos asignados implementadas.
- Tabla de gestores con seis acciones inline visibles: editar, eliminar, ver detalles, actualizar estado, permisos y cambiar contraseña. Botones compactos `h-8 w-8` con `gap-0.5`.
- La auditoría continúa accesible desde la ficha de detalle del gestor.
- `ActionButton` reutilizable: `h-8 w-8 rounded-lg border`, variante `danger` para eliminar.

## Archivos modificados en esta sesión

- `src/frontend/src/pages/admin/GestoresPage.tsx` — botones inline compactos, gap reducido.
- `src/frontend/src/pages/admin/LineasPage.tsx` — botones inline Editar + Eliminar, sin portal.
- `src/frontend/src/pages/admin/ProgramasPage.tsx` — botones inline Editar + Eliminar, sin portal.
- `src/frontend/src/pages/admin/ProductosPage.tsx` — botones inline Editar + Eliminar, sin portal.

## Estado de verificación

- `npm run build` pasa correctamente.
- Backend saludable en `/health`.
- Las acciones de gestores y la ficha de detalle fueron verificadas en navegador.
- El plan activo sembrado para el municipio de prueba es `PD-001` (`fba239a8-68a0-4d1b-9ff4-1b00857b629b`).

## Pendiente inmediato

- Reanudar backend tras el fix de `datetime.utcnow()` y probar CRUD de líneas/programas/productos en navegador.
- Completar pruebas CRUD encadenadas de línea → programa → producto y limpiar registros temporales.
- Validar Dashboard Gestor y Mis Productos con credenciales de gestor.
- Validar responsive en 390 px.

## Datos temporales conocidos

- Existe el gestor de prueba `GES-000002`; evaluar su eliminación cuando termine la validación integral.
