"""M2: app_user + sample user_id/review fields

Revision ID: a7c2e91d4f01
Revises: 0bb7a7326a13
Create Date: 2026-10-09 07:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a7c2e91d4f01'
down_revision: Union[str, None] = '0bb7a7326a13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('display_name', sa.String(length=32), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('role', sa.String(length=16), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone'),
    )
    op.add_column('sample', sa.Column('user_id', sa.Integer(), nullable=True))
    op.add_column('sample', sa.Column('review_note', sa.String(length=256),
                                      nullable=False, server_default=''))
    op.add_column('sample', sa.Column('reviewed_at', sa.DateTime(timezone=True),
                                      nullable=True))
    op.alter_column('sample', 'review_status', server_default='pending')
    op.create_foreign_key('fk_sample_user', 'sample', 'app_user',
                          ['user_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_sample_user', 'sample', type_='foreignkey')
    op.alter_column('sample', 'review_status', server_default='approved')
    op.drop_column('sample', 'reviewed_at')
    op.drop_column('sample', 'review_note')
    op.drop_column('sample', 'user_id')
    op.drop_table('app_user')
