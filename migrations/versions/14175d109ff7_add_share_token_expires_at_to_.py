"""add share_token_expires_at to questionnaires

Revision ID: 14175d109ff7
Revises: e6f7a8b9c0d1
Create Date: 2026-06-03 00:32:21.964027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14175d109ff7'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('questionnaires', sa.Column('share_token_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('questionnaires', 'share_token_expires_at')
