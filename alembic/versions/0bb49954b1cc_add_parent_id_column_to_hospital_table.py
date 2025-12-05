"""Add parent_id column to Hospital table

Revision ID: 0bb49954b1cc
Revises: 7bfb5335d207
Create Date: 2025-12-04 21:52:38.885402

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bb49954b1cc'
down_revision: Union[str, None] = '7bfb5335d207'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade():
    op.add_column(
        'hospitals',
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('hospitals.id'), nullable=True)
    )

def downgrade():
    op.drop_column('hospitals', 'parent_id')