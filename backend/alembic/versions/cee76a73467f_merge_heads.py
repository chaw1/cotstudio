"""merge_heads

Revision ID: cee76a73467f
Revises: 003, add_task_monitoring
Create Date: 2025-09-16 11:21:21.322123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cee76a73467f'
down_revision: Union[str, Sequence[str], None] = ('003', 'add_task_monitoring')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
