"""Add email confirmation + phone fields without batch ALTER

Revision ID: 1d03963c3adb
Revises: 32b50a3aa680
Create Date: 2025-05-26 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision = '1d03963c3adb'
down_revision = '32b50a3aa680'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Lägger till nya kolumner
    op.add_column('user', sa.Column('email', sa.String(120), nullable=False))
    op.add_column('user', sa.Column('show_email', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('user', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('user', sa.Column('show_phone', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('user', sa.Column('email_confirmed', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('user', sa.Column('email_token', sa.String(36), nullable=True))
    op.add_column('user', sa.Column('email_sent_at', sa.DateTime(), nullable=True))

    # 2) Gör username och password NOT NULL
    op.alter_column('user', 'username', existing_type=sa.String(150), nullable=False)
    op.alter_column('user', 'password', existing_type=sa.String(150), nullable=False)

    # 3) Ta bort server_default (valfritt)
    op.alter_column('user', 'show_email', server_default=None)
    op.alter_column('user', 'show_phone', server_default=None)
    op.alter_column('user', 'email_confirmed', server_default=None)


def downgrade():
    # backa kolumnerna i omvänd ordning
    op.alter_column('user', 'email_confirmed', existing_type=sa.Boolean(), nullable=True)
    op.drop_column('user', 'email_sent_at')
    op.drop_column('user', 'email_token')
    op.drop_column('user', 'email_confirmed')
    op.drop_column('user', 'show_phone')
    op.drop_column('user', 'phone_number')
    op.drop_column('user', 'show_email')
    op.drop_column('user', 'email')

    # återställ nullable för username/password
    op.alter_column('user', 'password', existing_type=sa.String(150), nullable=True)
    op.alter_column('user', 'username', existing_type=sa.String(150), nullable=True)
