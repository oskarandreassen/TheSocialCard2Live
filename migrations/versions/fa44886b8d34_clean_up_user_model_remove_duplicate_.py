"""Clean up User model – remove duplicate columns

Revision ID: fa44886b8d34
Revises: 1d03963c3adb
Create Date: 2025-05-28 23:59:04.827426

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa44886b8d34'
down_revision = '1d03963c3adb'
branch_labels = None
depends_on = None


def upgrade():
    # Remove any leftover temp table from previous failed upgrade
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_user")

    with op.batch_alter_table('user', schema=None) as batch_op:
        # Exempel: ta bort duplicerade kolumner eller annan cleanup
        # batch_op.drop_column('duplicate_field')
        pass


def downgrade():
    # Om rollback behöver återställa temp-tabellen, se till att den tas bort först
    op.execute("DROP TABLE IF EXISTS _alembic_tmp_user")

    with op.batch_alter_table('user', schema=None) as batch_op:
        # Exempel: lägg tillbaka duplicerade kolumner
        # batch_op.add_column(sa.Column('duplicate_field', sa.String(length=150)))
        pass

