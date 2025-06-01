"""Add main_public_link_id to User

Revision ID: b28d8f4e675c
Revises: 5f52078ede10
Create Date: 2025-05-31 17:54:33.078697

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b28d8f4e675c'
down_revision = '5f52078ede10'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns

def upgrade():
    if not column_exists('user', 'main_public_link_id'):
        op.add_column('user', sa.Column('main_public_link_id', sa.Integer(), nullable=True))
    # FK kan också kräva kontroll (men har sällan krock i SQLite)
    # op.create_foreign_key(None, 'user', 'link', ['main_public_link_id'], ['id'])

def downgrade():
    # Ta bort kolumnen om den finns
    if column_exists('user', 'main_public_link_id'):
        op.drop_column('user', 'main_public_link_id')
