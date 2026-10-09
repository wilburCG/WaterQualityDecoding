"""M5: official_section/official_reading/subscription/notification

Revision ID: e0a5b1c7d8f9
Revises: b8f3a72c9e02
Create Date: 2026-10-09 23:55:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e0a5b1c7d8f9'
down_revision: Union[str, None] = 'b8f3a72c9e02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'official_section',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('river', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('lng', sa.Numeric(10, 6), nullable=False),
        sa.Column('lat', sa.Numeric(10, 6), nullable=False),
        sa.Column('level', sa.String(length=16), nullable=False, server_default='市控'),
        sa.Column('source_org', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_table(
        'official_reading',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('values', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('overall_grade', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('source_url', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('note', sa.String(length=256), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['section_id'], ['official_section.id'],
                                ondelete='CASCADE'),
        sa.UniqueConstraint('section_id', 'observed_at',
                            name='uq_official_reading'),
    )
    op.create_table(
        'subscription',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.String(length=16), nullable=False),
        sa.Column('target_key', sa.String(length=64), nullable=False),
        sa.Column('target_label', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('alert_grade_from', sa.Integer(), nullable=False, server_default='4'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
        sa.UniqueConstraint('user_id', 'target_type', 'target_key',
                            name='uq_subscription'),
    )
    op.create_table(
        'notification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('kind', sa.String(length=16), nullable=False, server_default='new_data'),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('body', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('link', sa.String(length=256), nullable=False, server_default=''),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
    )
    op.create_index('ix_notification_user', 'notification',
                    ['user_id', 'is_read'])
    op.create_index('ix_notification_created', 'notification', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_notification_created', table_name='notification')
    op.drop_index('ix_notification_user', table_name='notification')
    op.drop_table('notification')
    op.drop_table('subscription')
    op.drop_table('official_reading')
    op.drop_table('official_section')
