"""Use decimal values for product goals and progress reports

Revision ID: 019_decimal_progress_values
Revises: 018_seed_dependencia_permissions
Create Date: 2026-10-03
"""

from alembic import op
import sqlalchemy as sa

revision = "019_decimal_progress_values"
down_revision = "018_seed_dependencia_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "productos",
        "linea_base",
        existing_type=sa.Integer(),
        type_=sa.Numeric(18, 4),
        existing_nullable=True,
        postgresql_using="linea_base::numeric(18,4)",
    )
    op.alter_column(
        "productos",
        "meta_cuatrienio",
        existing_type=sa.Integer(),
        type_=sa.Numeric(18, 4),
        existing_nullable=True,
        postgresql_using="meta_cuatrienio::numeric(18,4)",
    )
    op.execute("UPDATE avances_producto SET avance_valor = 0 WHERE avance_valor IS NULL")
    op.alter_column(
        "avances_producto",
        "avance_valor",
        existing_type=sa.Integer(),
        type_=sa.Numeric(18, 4),
        existing_nullable=True,
        nullable=False,
        server_default="0",
        postgresql_using="avance_valor::numeric(18,4)",
    )
    op.create_index(
        "ix_avances_producto_municipio_producto_estado",
        "avances_producto",
        ["municipio_id", "producto_id", "estado_revision"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_avances_producto_municipio_producto_estado",
        table_name="avances_producto",
    )
    op.alter_column(
        "avances_producto",
        "avance_valor",
        existing_type=sa.Numeric(18, 4),
        type_=sa.Integer(),
        existing_nullable=False,
        nullable=True,
        server_default=None,
        postgresql_using="round(avance_valor)::integer",
    )
    op.alter_column(
        "productos",
        "meta_cuatrienio",
        existing_type=sa.Numeric(18, 4),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="round(meta_cuatrienio)::integer",
    )
    op.alter_column(
        "productos",
        "linea_base",
        existing_type=sa.Numeric(18, 4),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="round(linea_base)::integer",
    )
