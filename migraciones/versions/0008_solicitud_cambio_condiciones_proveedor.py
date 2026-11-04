"""D-P3: condiciones del proveedor comunicadas para un cambio (opcionales).

Cambio aditivo: agrega una columna de texto que admite NULL a `solicitud_cambio`; no modifica ni borra ninguna fila existente (las
solicitudes ya registradas quedan sin condiciones). Coordinación la captura al evaluar la viabilidad y Administración la ve antes de autorizar.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('solicitud_cambio', sa.Column('condiciones_proveedor', sa.Text(), nullable=True))


def downgrade() -> None:
    # Solo descarta el texto de las condiciones: ninguna solicitud se elimina.
    op.drop_column('solicitud_cambio', 'condiciones_proveedor')
