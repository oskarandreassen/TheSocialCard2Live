"""Add analytics fields

Revision ID: ea0bbd5e7b8e
Revises: b28d8f4e675c
Create Date: 2025-06-19 20:22:00

"""
from alembic import op
import sqlalchemy as sa


def column_exists(table_name, column_name):
    """Return True if the given column exists on the table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns

# revision identifiers, used by Alembic.
revision = 'ea0bbd5e7b8e'
down_revision = 'b28d8f4e675c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user') as batch_op:
        if not column_exists('user', 'page_views'):
            batch_op.add_column(sa.Column('page_views', sa.Integer(), nullable=True, server_default='0'))
        if not column_exists('user', 'email_notifications'):
            batch_op.add_column(sa.Column('email_notifications', sa.Boolean(), nullable=True, server_default='1'))
    with op.batch_alter_table('link') as batch_op:
        if not column_exists('link', 'click_count'):
            batch_op.add_column(sa.Column('click_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    with op.batch_alter_table('link') as batch_op:
        batch_op.drop_column('click_count')
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('email_notifications')
        batch_op.drop_column('page_views')