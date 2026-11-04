"""Catálogo de proveedores: columna `activo`.

Cambio aditivo: agrega una columna con valor por defecto verdadero; no borra ni modifica ninguna fila existente (todos los proveedores
siguen activos). Un proveedor desactivado conserva sus asignaciones históricas, pero deja de proponerse para asignaciones nuevas.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('proveedor', sa.Column('activo', sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    # Solo descarta la bandera: ningún proveedor se elimina.
    op.drop_column('proveedor', 'activo')
