"""012_seed_catalogo_productos_programas

Siembra catálogo de ejemplo de líneas, programas y productos (idempotente)
y ajusta permisos del rol GESTOR_LIDER: solo consulta/asignación de
productos y programas (no crea ni elimina).

Revision ID: 012_seed_catalogo_productos_programas
Revises: 011_seed_gestor_role_and_coordinator_permissions
Create Date: 2026-09-23 00:00:00.000000

"""
from typing import Sequence, Union
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = '012_seed_catalogo'
down_revision: Union[str, None] = '011_gestor_role'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LINEAS = [
    ('LE-001', '01', 'Desarrollo Economico y Competitividad', 1),
    ('LE-002', '02', 'Infraestructura y Espacio Publico', 2),
    ('LE-003', '03', 'Desarrollo Social y Calidad de Vida', 3),
    ('LE-004', '04', 'Gestion Ambiental y Sostenibilidad', 4),
    ('LE-005', '05', 'Gobernanza y Participacion Ciudadana', 5),
]

# (codigo, nombre, sector, linea_codigo)
PROGRAMAS = [
    ('PRG-001', 'Fomento Productivo Local', 'Hacienda', 'LE-001'),
    ('PRG-002', 'Mejoramiento Vial Urbano', 'Obras Publicas', 'LE-002'),
    ('PRG-003', 'Atencion Integral en Salud', 'Salud', 'LE-003'),
    ('PRG-004', 'Gestion Integral de Residuos', 'Ambiente', 'LE-004'),
    ('PRG-005', 'Modernizacion de la Gestion Publica', 'Gobierno', 'LE-005'),
]

# (codigo, nombre, indicador, unidad, meta, programa_codigo)
PRODUCTOS = [
    ('PROD-001', 'Emprendimientos locales financiados', 'Numero de emprendimientos', 'unidades', 50, 'PRG-001'),
    ('PROD-002', 'Km de vias intervenidas', 'Kilometros intervenidos', 'km', 12, 'PRG-002'),
    ('PROD-003', 'Usuarios en programas de salud', 'Usuarios atendidos', 'personas', 8000, 'PRG-003'),
    ('PROD-004', 'Toneladas de residuos recicladas', 'Toneladas recicladas', 'ton', 300, 'PRG-004'),
    ('PROD-005', 'Tramites digitalizados', 'Tramites en linea', 'tramites', 40, 'PRG-005'),
]

COORDINATOR_READ_ASSIGN = [
    'PRODUCTO_VER',
    'PRODUCTO_EDITAR',
    'PROGRAMA_VER',
    'LINEA_ESTRATEGICA_VER',
]

COORDINATOR_NO_CREATE = [
    'PRODUCTO_CREAR',
    'PRODUCTO_ELIMINAR',
    'PROGRAMA_CREAR',
    'PROGRAMA_EDITAR',
    'PROGRAMA_ELIMINAR',
    'LINEA_ESTRATEGICA_CREAR',
    'LINEA_ESTRATEGICA_EDITAR',
    'LINEA_ESTRATEGICA_ELIMINAR',
]


def _municipio_plan(conn) -> tuple | None:
    row = conn.execute(
        sa.text(
            """
            SELECT m.id, p.id
            FROM municipios m
            LEFT JOIN planes_desarrollo p
              ON p.municipio_id = m.id AND p.deleted_at IS NULL
            WHERE m.codigo = '00000'
            ORDER BY p.created_at
            LIMIT 1
            """
        )
    ).first()
    return row


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)
    ids = _municipio_plan(conn)
    if ids is None:
        return
    municipio_id, plan_id = ids

    # --- Líneas estratégicas (solo si faltan) ---
    for codigo, numero, nombre, orden in LINEAS:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM lineas_estrategicas "
                "WHERE municipio_id = :m AND codigo = :c AND deleted_at IS NULL"
            ),
            {"m": municipio_id, "c": codigo},
        ).first()
        if exists:
            continue
        if plan_id is None:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO lineas_estrategicas
                (id, municipio_id, plan_desarrollo_id, codigo, numero, nombre,
                 orden, created_at, updated_at, version, estado)
                VALUES (:id, :m, :p, :c, :n, :nombre, :orden, :now, :now, 1, 'ACTIVA')
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "m": municipio_id,
                "p": plan_id,
                "c": codigo,
                "n": numero,
                "nombre": nombre,
                "orden": orden,
                "now": now,
            },
        )

    # --- Programas (solo si faltan) ---
    for codigo, nombre, sector, linea_codigo in PROGRAMAS:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM programas "
                "WHERE municipio_id = :m AND codigo = :c AND deleted_at IS NULL"
            ),
            {"m": municipio_id, "c": codigo},
        ).first()
        if exists:
            continue
        linea = conn.execute(
            sa.text(
                "SELECT id FROM lineas_estrategicas "
                "WHERE municipio_id = :m AND codigo = :lc AND deleted_at IS NULL"
            ),
            {"m": municipio_id, "lc": linea_codigo},
        ).first()
        if not linea:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO programas
                (id, municipio_id, linea_estrategica_id, codigo, nombre, sector,
                 created_at, updated_at, version, estado)
                VALUES (:id, :m, :l, :c, :nombre, :sector, :now, :now, 1, 'ACTIVO')
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "m": municipio_id,
                "l": linea[0],
                "c": codigo,
                "nombre": nombre,
                "sector": sector,
                "now": now,
            },
        )

    # --- Productos (solo si faltan; sin gestor asignado) ---
    for codigo, nombre, indicador, unidad, meta, programa_codigo in PRODUCTOS:
        exists = conn.execute(
            sa.text(
                "SELECT 1 FROM productos "
                "WHERE municipio_id = :m AND codigo = :c AND deleted_at IS NULL"
            ),
            {"m": municipio_id, "c": codigo},
        ).first()
        if exists:
            continue
        prog = conn.execute(
            sa.text(
                "SELECT id FROM programas "
                "WHERE municipio_id = :m AND codigo = :pc AND deleted_at IS NULL"
            ),
            {"m": municipio_id, "pc": programa_codigo},
        ).first()
        if not prog:
            continue
        dep = conn.execute(
            sa.text(
                "SELECT id FROM dependencias "
                "WHERE municipio_id = :m AND deleted_at IS NULL "
                "ORDER BY codigo LIMIT 1"
            ),
            {"m": municipio_id},
        ).first()
        conn.execute(
            sa.text(
                """
                INSERT INTO productos
                (id, municipio_id, programa_id, codigo, nombre, indicador,
                 unidad_medida, meta_cuatrienio, linea_base, dependencia_responsable_id,
                 gestor_lider_id, created_at, updated_at, version, estado)
                VALUES (:id, :m, :p, :c, :nombre, :ind, :unidad, :meta, 0, :dep,
                        NULL, :now, :now, 1, 'ACTIVO')
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "m": municipio_id,
                "p": prog[0],
                "c": codigo,
                "nombre": nombre,
                "ind": indicador,
                "unidad": unidad,
                "meta": meta,
                "dep": dep[0] if dep else None,
                "now": now,
            },
        )

    # --- Permisos coordinador: solo ver/asignar, no crear ---
    for permiso_codigo in COORDINATOR_READ_ASSIGN:
        conn.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (id, rol_id, permiso_id)
                SELECT gen_random_uuid(), r.id, p.id
                FROM roles r
                JOIN permisos p ON p.codigo = :permiso_codigo
                WHERE r.codigo = 'GESTOR_LIDER'
                  AND r.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM rol_permisos rp
                    WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
                  )
                """
            ),
            {"permiso_codigo": permiso_codigo},
        )

    conn.execute(
        sa.text(
            """
            DELETE FROM rol_permisos rp
            USING roles r, permisos p
            WHERE rp.rol_id = r.id
              AND rp.permiso_id = p.id
              AND r.codigo = 'GESTOR_LIDER'
              AND p.codigo = ANY(:codigos)
            """
        ),
        {"codigos": COORDINATOR_NO_CREATE},
    )


def downgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for codigo, *_ in reversed(PRODUCTOS):
        conn.execute(
            sa.text(
                "DELETE FROM productos WHERE codigo = :c AND gestor_lider_id IS NULL "
                "AND deleted_at IS NULL"
            ),
            {"c": codigo},
        )

    for codigo, *_ in reversed(PROGRAMAS):
        conn.execute(
            sa.text(
                "DELETE FROM programas WHERE codigo = :c AND deleted_at IS NULL"
            ),
            {"c": codigo},
        )

    for codigo, *_ in reversed(LINEAS):
        conn.execute(
            sa.text(
                "DELETE FROM lineas_estrategicas WHERE codigo = :c AND deleted_at IS NULL"
            ),
            {"c": codigo},
        )

    for permiso_codigo in COORDINATOR_NO_CREATE:
        conn.execute(
            sa.text(
                """
                INSERT INTO rol_permisos (id, rol_id, permiso_id)
                SELECT gen_random_uuid(), r.id, p.id
                FROM roles r
                JOIN permisos p ON p.codigo = :permiso_codigo
                WHERE r.codigo = 'GESTOR_LIDER'
                  AND r.deleted_at IS NULL
                  AND p.deleted_at IS NULL
                  AND NOT EXISTS (
                    SELECT 1 FROM rol_permisos rp
                    WHERE rp.rol_id = r.id AND rp.permiso_id = p.id
                  )
                """
            ),
            {"permiso_codigo": permiso_codigo},
        )
