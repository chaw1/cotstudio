"""Add knowledge graph models

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create kg_entities table
    op.create_table('kg_entities',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('neo4j_node_id', sa.String(255), nullable=True),
        sa.Column('embedding_vector', sa.JSON(), nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for kg_entities
    op.create_index('idx_kg_entity_name_type', 'kg_entities', ['name', 'entity_type'])
    op.create_index('idx_kg_entity_neo4j_id', 'kg_entities', ['neo4j_node_id'])
    op.create_index(op.f('ix_kg_entities_neo4j_node_id'), 'kg_entities', ['neo4j_node_id'], unique=True)

    # Create kg_relations table
    op.create_table('kg_relations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('source_entity_id', sa.String(36), nullable=False),
        sa.Column('target_entity_id', sa.String(36), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('properties', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('neo4j_relation_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_entity_id'], ['kg_entities.id'], ),
        sa.ForeignKeyConstraint(['target_entity_id'], ['kg_entities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for kg_relations
    op.create_index('idx_kg_relation_entities', 'kg_relations', ['source_entity_id', 'target_entity_id'])
    op.create_index('idx_kg_relation_type', 'kg_relations', ['relation_type'])
    op.create_index('idx_kg_relation_neo4j_id', 'kg_relations', ['neo4j_relation_id'])
    op.create_index(op.f('ix_kg_relations_neo4j_relation_id'), 'kg_relations', ['neo4j_relation_id'], unique=True)

    # Create kg_extractions table
    op.create_table('kg_extractions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('cot_item_id', sa.String(36), nullable=False),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('relation_id', sa.String(36), nullable=True),
        sa.Column('extraction_method', sa.String(100), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('extraction_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cot_item_id'], ['cot_items.id'], ),
        sa.ForeignKeyConstraint(['entity_id'], ['kg_entities.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['relation_id'], ['kg_relations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for kg_extractions
    op.create_index('idx_kg_extraction_cot', 'kg_extractions', ['cot_item_id'])
    op.create_index('idx_kg_extraction_project', 'kg_extractions', ['project_id'])
    op.create_index('idx_kg_extraction_entity', 'kg_extractions', ['entity_id'])
    op.create_index('idx_kg_extraction_relation', 'kg_extractions', ['relation_id'])

    # Create kg_embeddings table
    op.create_table('kg_embeddings',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('relation_id', sa.String(36), nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_vector', sa.JSON(), nullable=False),
        sa.Column('vector_dimension', sa.Integer(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('embedding_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['entity_id'], ['kg_entities.id'], ),
        sa.ForeignKeyConstraint(['relation_id'], ['kg_relations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for kg_embeddings
    op.create_index('idx_kg_embedding_entity', 'kg_embeddings', ['entity_id'])
    op.create_index('idx_kg_embedding_relation', 'kg_embeddings', ['relation_id'])
    op.create_index('idx_kg_embedding_model', 'kg_embeddings', ['embedding_model'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('kg_embeddings')
    op.drop_table('kg_extractions')
    op.drop_table('kg_relations')
    op.drop_table('kg_entities')