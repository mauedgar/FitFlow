"""Update enums

Revision ID: 38d9796100f0
Revises: 3a6ad3ed45ab
Create Date: 2026-08-02 04:12:40.871209

"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '38d9796100f0'
down_revision: Union[str, Sequence[str], None] = '3a6ad3ed45ab'  # noqa: UP007
branch_labels: Union[str, Sequence[str], None] = None  # noqa: UP007
depends_on: Union[str, Sequence[str], None] = None  # noqa: UP007

def upgrade():

    # 1. Crear nuevos ENUMs con los valores correctos
    op.execute("""
        CREATE TYPE bookingstatus_new AS ENUM (
            'confirmed',
            'cancelled',
            'attended',
            'no_show'
        );
    """)

    op.execute("""
        CREATE TYPE membershipplan_new AS ENUM (
            'gym_only',
            'classes',
            'premium',
            'personalized'
        );
    """)

    op.execute("""
        CREATE TYPE userrole_new AS ENUM (
            'admin',
            'teacher',
            'client',
            'front_desk'
        );
    """)

    # 2. Convertir columnas ENUM a TEXT temporalmente

    op.execute("ALTER TABLE bookings ALTER COLUMN status TYPE TEXT;")
    op.execute("ALTER TABLE memberships ALTER COLUMN plan TYPE TEXT;")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE TEXT;")

    # 3. Normalizar valores existentes

    # BOOKING STATUS
    op.execute("UPDATE bookings SET status = LOWER(status);")
    op.execute("UPDATE bookings SET status = 'cancelled' WHERE status = 'pending';")

    # MEMBERSHIP PLAN
    op.execute("UPDATE memberships SET plan = LOWER(plan);")
    op.execute("UPDATE memberships SET plan = 'gym_only' WHERE plan = 'basic';")
    op.execute("UPDATE memberships SET plan = 'classes' WHERE plan = 'plus';")
    op.execute("UPDATE memberships SET plan = 'premium' WHERE plan = 'premium';")

    # USER ROLE
    op.execute("UPDATE users SET role = LOWER(role);")
    op.execute("UPDATE users SET role = 'teacher' WHERE role = 'trainer';")

    # 4. Convertir columnas TEXT → nuevos ENUMs

    op.execute("""
        ALTER TABLE bookings
        ALTER COLUMN status TYPE bookingstatus_new
        USING status::bookingstatus_new;
    """)

    op.execute("""
        ALTER TABLE memberships
        ALTER COLUMN plan TYPE membershipplan_new
        USING plan::membershipplan_new;
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE userrole_new
        USING role::userrole_new;
    """)

    # 5. Eliminar ENUMs viejos
    op.execute("DROP TYPE IF EXISTS bookingstatus;")
    op.execute("DROP TYPE IF EXISTS membershipplan;")
    op.execute("DROP TYPE IF EXISTS userrole;")

    # 6. Renombrar los nuevos ENUMs a los nombres originales
    op.execute("ALTER TYPE bookingstatus_new RENAME TO bookingstatus;")
    op.execute("ALTER TYPE membershipplan_new RENAME TO membershipplan;")
    op.execute("ALTER TYPE userrole_new RENAME TO userrole;")


def downgrade():
    pass