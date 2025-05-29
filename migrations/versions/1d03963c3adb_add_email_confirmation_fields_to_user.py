"""
Revision: Add email confirmation fields to User, backfill existing NULL emails
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1d03963c3adb'
down_revision = '32b50a3aa680'
branch_labels = None
depends_on = None


def upgrade():
    # 1) Backfill any NULL emails with a unique placeholder using user ID
    op.execute(
        """
        UPDATE user
           SET email = printf('user%d@local.invalid', id)
         WHERE email IS NULL
        """
    )

    # 2) Alter the table: add confirmation columns and enforce NOT NULL + UNIQUE on email
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_confirmed', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('email_token', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('email_sent_at', sa.DateTime(), nullable=True))
        batch_op.alter_column(
            'email',
            existing_type=sa.VARCHAR(length=120),
            nullable=False,
            existing_nullable=True
        )
        batch_op.create_unique_constraint('uq_user_email', ['email'])


def downgrade():
    # Roll back the schema changes
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_email', type_='unique')
        batch_op.alter_column(
            'email',
            existing_type=sa.VARCHAR(length=120),
            nullable=True
        )
        batch_op.drop_column('email_sent_at')
        batch_op.drop_column('email_token')
        batch_op.drop_column('email_confirmed')
