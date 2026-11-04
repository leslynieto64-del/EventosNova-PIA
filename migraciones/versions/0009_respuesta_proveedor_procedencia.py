"""S-5: procedencia de la respuesta del proveedor.

Cambio aditivo: agrega columnas que admiten NULL a `evento_servicio_contratado` y tres CHECK que solo comprueban las filas que ya tengan
respuesta; no modifica ni borra ninguna fila existente (las respuestas anteriores quedan sin procedencia registrada). Permite distinguir una
respuesta directa del proveedor de una que Coordinación registró a partir de lo que el proveedor le comunicó, con el medio, la cuenta y la fecha.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None

TABLA = 'evento_servicio_contratado'


def upgrade() -> None:
    op.add_column(TABLA, sa.Column('respuesta_disponible', sa.Boolean(), nullable=True))
    op.add_column(TABLA, sa.Column('respuesta_origen', sa.Text(), nullable=True))
    op.add_column(TABLA, sa.Column('respuesta_medio', sa.Text(), nullable=True))
    op.add_column(TABLA, sa.Column('respuesta_registrada_por_id', sa.Text(), nullable=True))
    op.add_column(TABLA, sa.Column('respuesta_registrada_por_nombre', sa.Text(), nullable=True))
    op.add_column(TABLA, sa.Column('respuesta_fecha', sa.DateTime(), nullable=True))
    op.create_check_constraint('ck_evento_servicio_contratado_respuesta_completa', TABLA,
                               '(respuesta_disponible IS NULL AND respuesta_origen IS NULL AND respuesta_registrada_por_id IS NULL AND '
                               'respuesta_registrada_por_nombre IS NULL AND respuesta_fecha IS NULL) OR (respuesta_disponible IS NOT NULL AND '
                               'respuesta_origen IS NOT NULL AND respuesta_registrada_por_id IS NOT NULL AND respuesta_registrada_por_nombre IS NOT NULL '
                               'AND respuesta_fecha IS NOT NULL)')
    op.create_check_constraint('ck_evento_servicio_contratado_respuesta_origen_valido', TABLA,
                               "respuesta_origen IS NULL OR respuesta_origen IN ('Proveedor', 'Coordinación', 'Sin identificar')")
    op.create_check_constraint('ck_evento_servicio_contratado_respuesta_medio_segun_origen', TABLA,
                               "respuesta_origen IS NULL OR ((respuesta_origen = 'Coordinación') = (respuesta_medio IS NOT NULL))")


def downgrade() -> None:
    # Solo descarta la procedencia de las respuestas: ningún servicio ni su estado se modifica.
    op.drop_constraint('ck_evento_servicio_contratado_respuesta_medio_segun_origen', TABLA, type_='check')
    op.drop_constraint('ck_evento_servicio_contratado_respuesta_origen_valido', TABLA, type_='check')
    op.drop_constraint('ck_evento_servicio_contratado_respuesta_completa', TABLA, type_='check')
    for columna in ('respuesta_fecha', 'respuesta_registrada_por_nombre', 'respuesta_registrada_por_id', 'respuesta_medio',
                    'respuesta_origen', 'respuesta_disponible'):
        op.drop_column(TABLA, columna)
