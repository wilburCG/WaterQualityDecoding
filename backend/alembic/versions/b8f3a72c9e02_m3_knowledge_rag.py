"""M3: knowledge_doc / knowledge_chunk(embedding float8[]) / ask_query

Revision ID: b8f3a72c9e02
Revises: a7c2e91d4f01
Create Date: 2026-10-09 10:00:00.000000

注：向量存储为 PostgreSQL 原生 float8[]，余弦相似度在应用层用 numpy 计算
（知识库规模小，无需 pgvector 扩展）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b8f3a72c9e02'
down_revision: Union[str, None] = 'a7c2e91d4f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'knowledge_doc',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('source', sa.String(length=128), nullable=False, server_default=''),
        sa.Column('source_url', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('category', sa.String(length=32), nullable=False, server_default='science'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'knowledge_chunk',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.ARRAY(sa.Float(precision=8)), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['doc_id'], ['knowledge_doc.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('doc_id', 'chunk_index', name='uq_knowledge_chunk'),
    )
    op.create_table(
        'ask_query',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('client_id', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('question', sa.String(length=512), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False, server_default=''),
        sa.Column('citations', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['app_user.id']),
    )
    op.create_index('ix_ask_query_created', 'ask_query', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_ask_query_created', table_name='ask_query')
    op.drop_table('ask_query')
    op.drop_table('knowledge_chunk')
    op.drop_table('knowledge_doc')
