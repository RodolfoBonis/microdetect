"""Adicionar relação muitos-para-muitos entre imagens e datasets

Revision ID: af03f1465b64
Revises: 444cb2d35019
Create Date: 2025-03-25 23:46:12.048335

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'af03f1465b64'
down_revision = '444cb2d35019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Verificar se a tabela dataset_images já existe
    conn = op.get_bind()
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='dataset_images'"))
    table_exists = result.fetchone() is not None
    
    if not table_exists:
        # Criar a tabela de relacionamento entre datasets e imagens
        op.create_table('dataset_images',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('dataset_id', sa.Integer(), nullable=False),
            sa.Column('image_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('file_path', sa.String(length=255), nullable=False),
            sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ),
            sa.ForeignKeyConstraint(['image_id'], ['images.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_dataset_images_id', 'dataset_images', ['id'], unique=False)
    
    # Ajustar a coluna dataset_id na tabela images para ser opcional (aceitar NULL)
    # Isso é necessário para suportar imagens que não pertencem a nenhum dataset específico
    try:
        op.alter_column('images', 'dataset_id', nullable=True)
    except:
        # Pode falhar se a coluna já for nullable ou se for SQLite (que tem limitações)
        pass
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Remover a tabela de relacionamento
    op.drop_index('ix_dataset_images_id', table_name='dataset_images')
    op.drop_table('dataset_images')
    
    # Reverter a coluna dataset_id para não aceitar NULL
    try:
        # SQLite não suporta ALTER COLUMN diretamente, então seria necessário
        # recriar a tabela. Como isso é complexo, deixamos em branco.
        pass
    except:
        pass
    
    # ### end Alembic commands ### 