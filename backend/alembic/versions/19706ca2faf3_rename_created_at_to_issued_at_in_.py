"""Rename created_at to issued_at in credentials

Revision ID: 19706ca2faf3
Revises: 8b6842a34b83
Create Date: 2026-08-31 22:14:24.216106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '19706ca2faf3'
down_revision: Union[str, Sequence[str], None] = '8b6842a34b83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('identity_credential') as batch_op:
        batch_op.add_column(sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.drop_column('created_at')

def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('identity_credential') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))
        batch_op.drop_column('issued_at')
    # ### end Alembic commands ###
