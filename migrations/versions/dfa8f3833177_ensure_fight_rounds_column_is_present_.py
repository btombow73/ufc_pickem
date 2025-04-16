"""Ensure fight_rounds column is present in the fight table

Revision ID: dfa8f3833177
Revises: 
Create Date: 2025-04-08 14:01:21.144719
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfa8f3833177'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Ensure the 'fight_rounds' column exists in the 'fight' table
    with op.batch_alter_table('fight', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fight_rounds', sa.Integer(), nullable=False, default=3))
    
    # Alter existing columns in the 'fighter' table
    with op.batch_alter_table('fighter', schema=None) as batch_op:
        batch_op.alter_column('wins', type_=sa.BigInteger)
        batch_op.alter_column('losses', type_=sa.BigInteger)
        batch_op.alter_column('draws', type_=sa.BigInteger)
    
    # Optionally: Add or modify other columns as needed
    # For example, if weight_class was not already added in the model
    with op.batch_alter_table('fighter', schema=None) as batch_op:
        batch_op.add_column(sa.Column('weight_class', sa.String(length=50), nullable=True))
        
    # Other changes can be added here, such as fixing data types or adding new columns


def downgrade():
    # Remove the 'fight_rounds' column from the 'fight' table
    with op.batch_alter_table('fight', schema=None) as batch_op:
        batch_op.drop_column('fight_rounds')
    
    # Revert any changes made to the 'fighter' table
    with op.batch_alter_table('fighter', schema=None) as batch_op:
        batch_op.alter_column('wins', type_=sa.Integer)
        batch_op.alter_column('losses', type_=sa.Integer)
        batch_op.alter_column('draws', type_=sa.Integer)
        
    # Optionally: Remove the 'weight_class' column if it was added
    with op.batch_alter_table('fighter', schema=None) as batch_op:
        batch_op.drop_column('weight_class')
