"""rename enum types

Revision ID: 3a6ad3ed45ab
Revises: f5453ed20cdc
Create Date: 2026-08-01 01:20:50.263561
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3a6ad3ed45ab"
down_revision: Union[str, Sequence[str], None] = "f5453ed20cdc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Mapeo: nombre_actual -> nombre_objetivo
RENAME_MAP = {
    "allowedplan_enum": "allowedplan",
    "activitytype_enum": "activitytype",
    "classsessionstatus_enum": "classsessionstatus",
    "membershipstatus_enum": "membershipstatus",
    "difficultylevel_enum_new": "difficultylevel",
}


def upgrade() -> None:
    """Renombra los tipos ENUM a su denominación definitiva (sin sufijos)."""
    for old_name, new_name in RENAME_MAP.items():
        # Elimina cualquier tipo previo con el nombre destino para evitar colisiones
        op.execute(f'DROP TYPE IF EXISTS "{new_name}" CASCADE;')
        # Renombra el tipo actual
        op.execute(f'ALTER TYPE "{old_name}" RENAME TO "{new_name}";')


def downgrade() -> None:
    """Vuelve a los nombres con sufijos (_enum / _enum_new)."""
    for old_name, new_name in reversed(list(RENAME_MAP.items())):
        # Elimina el tipo con sufijo por si quedó de una reversión previa
        op.execute(f'DROP TYPE IF EXISTS "{old_name}" CASCADE;')
        # Renombra el tipo limpio de vuelta al nombre anterior
        op.execute(f'ALTER TYPE "{new_name}" RENAME TO "{old_name}";')