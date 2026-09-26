"""016_seed_avances_evidencias_ejemplo

Siembra avances de ejemplo con diferentes estados de revisión y
evidencias de referencia para el catálogo de productos (idempotente).

Uso típico: entorno de demostración o pruebas manuales.

Revision ID: 016_seed_avances_evidencias_ejemplo
Revises: 015
Create Date: 2026-09-23 00:00:00.000000
"""
from typing import Sequence, Union
from datetime import datetime, timezone
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = '016_seed_avances_evidencias'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (codigo_producto, avance_porcentaje, avance_valor, periodo, estado_revision,
#  observaciones, observaciones_revision)
AVANCES_EJEMPLO = [
    (
        'PROD-001', 65.0, 32500000, 'Julio - Septiembre 2026', 'APROBADO',
        'Se financiaron 33 emprendimientos con enfoque de género.',
        None,
    ),
    (
        'PROD-002', 42.5, 51000000, 'Julio - Septiembre 2026', 'PENDIENTE',
        'Avance en tramo norte: 5.1 km de 12 km proyectados.',
        None,
    ),
    (
        'PROD-003', 78.0, 62400000, 'Abril - Junio 2026', 'RECHAZADO',
        'Atención a 6240 usuarios en programas de salud.',
        'Faltan actas de firma de convenios con las IPS.',
    ),
    (
        'PROD-004', 100.0, 90000000, 'Enero - Diciembre 2026', 'APROBADO',
        'Meta anual cumplida: 300 toneladas recicladas.',
        None,
    ),
    (
        'PROD-005', 25.0, 10000000, 'Julio - Septiembre 2026', 'PENDIENTE',
        '10 trámites digitalizados de 40 proyectados.',
        None,
    ),
]

# (codigo_producto, indice_avance) -> evidencias de ejemplo
# Solo se crean filas de metadatos; los archivos no existen en disco
# (url es un placeholder para demo/UI).
EVIDENCIAS_EJEMPLO = {
    'PROD-001': [
        ('informe_financiamiento.pdf', 'application/pdf', 'Informe trimestral de financiamientos', 245760),
        ('foto_emprendimiento.png', 'image/png', 'Fotografía de emprendimiento beneficiado', 184320),
    ],
    'PROD-002': [
        ('acta_obra_vial.pdf', 'application/pdf', 'Acta de avance de obra vial', 312320),
        ('croquis_tramo.png', 'image/png', 'Croquis del tramo intervenido', 156672),
    ],
    'PROD-003': [
        ('convenios_ips.pdf', 'application/pdf', 'Convenios firmados con IPS', 421888),
    ],
    'PROD-004': [
        ('certificado_reciclaje.pdf', 'application/pdf', 'Certificado de cumplimiento meta anual', 198656),
        ('balance_mensual.csv', 'text/csv', 'Balance mensual de toneladas', 24576),
    ],
    'PROD-005': [
        ('listado_tramites.pdf', 'application/pdf', 'Listado de trámites digitalizados', 167936),
    ],
}


def _municipio_gestor_producto(conn, codigo_producto: str):
    """Retorna (municipio_id, gestor_id, producto_id) o None."""
    row = conn.execute(
        sa.text(
            """
            SELECT p.municipio_id, p.gestor_lider_id, p.id
            FROM productos p
            WHERE p.codigo = :c AND p.deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"c": codigo_producto},
    ).first()
    if not row or not row[1]:
        return None
    return row[0], row[1], row[2]


def _municipio_admin(conn):
    """Retorna (municipio_id, admin_usuario_id) del primer admin municipal."""
    row = conn.execute(
        sa.text(
            """
            SELECT m.id, u.id
            FROM municipios m
            JOIN usuarios u ON u.municipio_id = m.id
            JOIN usuario_roles ur ON ur.usuario_id = u.id
            JOIN roles r ON r.id = ur.rol_id
            WHERE r.codigo = 'ADMINISTRADOR_MUNICIPAL'
              AND u.deleted_at IS NULL
              AND m.deleted_at IS NULL
            LIMIT 1
            """
        )
    ).first()
    if not row:
        # Fallback: cualquier usuario del municipio 00000
        row = conn.execute(
            sa.text(
                """
                SELECT m.id, u.id
                FROM municipios m
                JOIN usuarios u ON u.municipio_id = m.id
                WHERE m.codigo = '00000' AND u.deleted_at IS NULL
                LIMIT 1
                """
            )
        ).first()
    return row


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    for (
        codigo_producto,
        avance_porcentaje,
        avance_valor,
        periodo,
        estado_revision,
        observaciones,
        observaciones_revision,
    ) in AVANCES_EJEMPLO:
        ctx = _municipio_gestor_producto(conn, codigo_producto)
        if ctx is None:
            continue
        municipio_id, gestor_id, producto_id = ctx

        exists = conn.execute(
            sa.text(
                """
                SELECT 1 FROM avances_producto
                WHERE producto_id = :p AND periodo = :per AND deleted_at IS NULL
                """
            ),
            {"p": producto_id, "per": periodo},
        ).first()
        if exists:
            continue

        admin_ctx = _municipio_admin(conn)
        registrado_por = admin_ctx[1] if admin_ctx else None

        avance_id = uuid.uuid4()
        now_naive = now.replace(tzinfo=None)
        conn.execute(
            sa.text(
                """
                INSERT INTO avances_producto (
                    id, municipio_id, producto_id, gestor_lider_id,
                    avance_porcentaje, avance_valor, observaciones,
                    estado, registrado_por,
                    indicador, periodo, fecha_registro,
                    estado_revision, observaciones_revision,
                    created_at, updated_at, version
                ) VALUES (
                    :id, :m, :p, :g,
                    :pct, :val, :obs,
                    'REGISTRADO', :reg,
                    NULL, :periodo, :now_tz,
                    :estado_rev, :obs_rev,
                    :now_naive, :now_naive, 1
                )
                """
            ),
            {
                "id": avance_id,
                "m": municipio_id,
                "p": producto_id,
                "g": gestor_id,
                "pct": avance_porcentaje,
                "val": avance_valor,
                "obs": observaciones,
                "reg": registrado_por,
                "periodo": periodo,
                "now_tz": now,
                "now_naive": now_naive,
                "estado_rev": estado_revision,
                "obs_rev": observaciones_revision,
            },
        )

        # Evidencias de ejemplo para este producto
        for nombre, tipo, descripcion, tamano in EVIDENCIAS_EJEMPLO.get(codigo_producto, []):
            ev_exists = conn.execute(
                sa.text(
                    """
                    SELECT 1 FROM evidencias
                    WHERE avance_id = :a AND nombre = :n AND deleted_at IS NULL
                    """
                ),
                {"a": avance_id, "n": nombre},
            ).first()
            if ev_exists:
                continue

            # Placeholder: archivo simulado (no existe en disco)
            rel_url = f"{municipio_id}/{avance_id}/demo_{uuid.uuid4().hex[:8]}_{nombre}"
            now_naive = now.replace(tzinfo=None)
            conn.execute(
                sa.text(
                    """
                    INSERT INTO evidencias (
                        id, avance_id, municipio_id,
                        nombre, tipo, url, descripcion,
                        tamano_original, tamano_almacenado,
                        optimizada, subida_por,
                        created_at, updated_at, version, estado
                    ) VALUES (
                        :id, :a, :m,
                        :nombre, :tipo, :url, :desc,
                        :tam_orig, :tam_alm,
                        false, :subida_por,
                        :now_naive, :now_naive, 1, 'ACTIVO'
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "a": avance_id,
                    "m": municipio_id,
                    "nombre": nombre,
                    "tipo": tipo,
                    "url": rel_url,
                    "desc": descripcion,
                    "tam_orig": tamano,
                    "tam_alm": tamano,
                    "subida_por": registrado_por,
                    "now_naive": now_naive,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()

    # Eliminar evidencias de demo (url con prefijo demo_)
    conn.execute(
        sa.text(
            """
            DELETE FROM evidencias
            WHERE url LIKE '%/demo_%'
            """
        )
    )

    # Eliminar avances de ejemplo (identificables por periodo + % de la lista)
    for codigo_producto, _, _, periodo, *_ in reversed(AVANCES_EJEMPLO):
        conn.execute(
            sa.text(
                """
                DELETE FROM avances_producto a
                USING productos p
                WHERE a.producto_id = p.id
                  AND p.codigo = :c
                  AND a.periodo = :per
                  AND a.deleted_at IS NULL
                """
            ),
            {"c": codigo_producto, "per": periodo},
        )
