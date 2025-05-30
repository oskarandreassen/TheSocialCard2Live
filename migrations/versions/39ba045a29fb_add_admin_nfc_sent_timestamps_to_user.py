"""Add admin/nfc_sent/timestamps to User

Revision ID: 39ba045a29fb
Revises: fa44886b8d34
Create Date: 2025-05-30 12:29:53.230307
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '39ba045a29fb'
down_revision = 'fa44886b8d34'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Lägg till kolumner utan default, men med server_default för booleans
    op.add_column(
        'user',
        sa.Column('is_admin', sa.Boolean(), nullable=False,
                  server_default=sa.text('0'))
    )
    op.add_column(
        'user',
        sa.Column('nfc_sent', sa.Boolean(), nullable=False,
                  server_default=sa.text('0'))
    )
    # timestamps som nullable till att börja med
    op.add_column(
        'user',
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'user',
        sa.Column('last_login', sa.DateTime(), nullable=True)
    )

    # 2) Backfilla befintliga rader: sätt created_at = now
    op.execute("""
        UPDATE "user"
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
    """)

    # 3) Hårdkoda ditt admin-konto
    op.execute("""
        UPDATE "user"
        SET is_admin = 1
        WHERE username = 'oskaröstlind'
          AND email    = 'oskarandreassen01@gmail.com';
    """)

    # 4) Rulla bort server_default så det bara gäller vid migreringen
    op.alter_column('user', 'is_admin',   server_default=None)
    op.alter_column('user', 'nfc_sent',   server_default=None)

    # 5) Gör created_at non-nullable
    op.alter_column('user', 'created_at', nullable=False)


def downgrade():
    # Ta bort fälten i omvänd ordning
    op.drop_column('user', 'last_login')
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'nfc_sent')
    op.drop_column('user', 'is_admin')
