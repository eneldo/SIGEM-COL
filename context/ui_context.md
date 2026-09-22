# Contexto UI de SIGEM Colombia

## Identidad visual

- Verde institucional: `--pine #0F3D3B`.
- Ocre: `--ochre #B9852F`.
- Fondo: `--paper #F5F3EC`.
- Éxito: `--done #3E7C5A`.
- Advertencia: `--warn #B5502E`.
- Tipografías: Atkinson Hyperlegible y Source Serif 4.

## Patrones vigentes

- Encabezados principales en panel verde, bordes redondeados y acciones primarias en ocre.
- Tarjetas KPI blancas con borde sutil y jerarquía tipográfica institucional.
- Tablas dentro de contenedores con `overflow-x-auto` para conservar funcionalidad en móvil.
- Modales accesibles con título, descripción, cierre por botón y cierre al pulsar el fondo.
- Acciones inline en todas las tablas CRUD (Líneas, Programas, Productos, Gestores): botones `h-8 w-8` con `gap-0.5`, sin menús portales.
- `ActionButton` reutilizable: borde `border-line`, texto `text-pine`, hover `hover:bg-forest-soft`. Variante `danger` con borde `border-warn/20` y fondo `hover:bg-warn-soft`.
- La ficha de detalle conserva el acceso a la auditoría del gestor.

## Navegación

- El sidebar puede cerrarse en escritorio y abrirse como drawer con overlay en móvil.
- La ruta `/gestor/productos` está activa y enlazada desde la navegación del gestor.
