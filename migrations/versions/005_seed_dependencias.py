"""005_seed_dependencias

Revision ID: 005_seed_dependencias
Revises: 004_normalize_role_codes
Create Date: 2026-09-20 00:00:00.000000

Se siembran dependencias municipales de ejemplo para el municipio 00000,
necesarias para el formulario de Gestores Líderes y sus catálogos.

"""
from typing import Sequence, Union
from datetime import datetime
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = '005_seed_dependencias'
down_revision: Union[str, None] = '004_normalize_role_codes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DEPENDENCIAS = [
    ('DEP-001', 'Secretaría de Planeación', 'Entidad encargada de la planificación del desarrollo municipal'),
    ('DEP-002', 'Secretaría de Hacienda', 'Entidad encargada de la gestión financiera y presupuestal'),
    ('DEP-003', 'Secretaría de Gobierno', 'Entidad encargada del orden público y la convivencia ciudadana'),
    ('DEP-004', 'Secretaría de Infraestructura y Obras Públicas', 'Entidad encargada de obras civiles y espacio público'),
    ('DEP-005', 'Secretaría de Desarrollo Social', 'Entidad encargada de programas de inclusión y bienestar social'),
]


def upgrade() -> None:
    conn = op.get_bind()
    municipio = conn.execute(
        sa.text("SELECT id FROM municipios WHERE codigo = :codigo"),
        {"codigo": "00000"},
    ).first()

    if municipio is None:
        return

    municipio_id = municipio[0]
    now = datetime.utcnow()

    for codigo, nombre, descripcion in DEPENDENCIAS:
        dep_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO dependencias "
                "(id, municipio_id, codigo, nombre, descripcion, dependencia_padre_id, nivel, "
                "created_at, updated_at, version, estado, deleted_at, deleted_by) "
                "VALUES (:id, :municipio_id, :codigo, :nombre, :descripcion, NULL, 1, "
                ":now, :now, 1, 'ACTIVA', NULL, NULL)"
            ),
            {
                "id": dep_id,
                "municipio_id": municipio_id,
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "now": now,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    codigos = [codigo for codigo, _, _ in DEPENDENCIAS]
    conn.execute(
        sa.text("DELETE FROM dependencias WHERE codigo IN :codigos"),
        {"codigos": tuple(codigos)},
    )