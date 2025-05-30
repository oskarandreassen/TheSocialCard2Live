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
    bind = op.get_bind()
    insp = inspect(bind)
    existing = {col['name'] for col in insp.get_columns('user')}

    # Lägg bara till kolumner om de inte redan finns
    if 'is_admin' not in existing:
        op.add_column('user',
            sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    if 'nfc_sent' not in existing:
        op.add_column('user',
            sa.Column('nfc_sent', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    if 'created_at' not in existing:
        op.add_column('user',
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.text('CURRENT_TIMESTAMP'))
        )
    if 'last_login' not in existing:
        op.add_column('user',
            sa.Column('last_login', sa.DateTime(), nullable=True)
        )

    # Backfill och eventuella custom-uppdateringar
    op.execute("""
        UPDATE "user"
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL;
    """)
    op.execute("""
        UPDATE "user"
        SET is_admin = 1
        WHERE username = 'oskaröstlind'
          AND email    = 'oskarandreassen01@gmail.com';
    """)

    # Ta bort server_default för kolumnerna, men bara på andra dialekter än SQLite
    if bind.dialect.name != 'sqlite':
        op.alter_column('user', 'is_admin',   server_default=None)
        op.alter_column('user', 'nfc_sent',   server_default=None)
        op.alter_column('user', 'created_at', server_default=None)


def downgrade():
    # Ta bort fälten i omvänd ordning
    op.drop_column('user', 'last_login')
    op.drop_column('user', 'created_at')
    op.drop_column('user', 'nfc_sent')
    op.drop_column('user', 'is_admin')
