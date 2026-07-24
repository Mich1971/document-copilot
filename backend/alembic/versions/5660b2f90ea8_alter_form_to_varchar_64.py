"""alter_form_to_varchar_64

Revision ID: 5660b2f90ea8
Revises: 5854003476ac
Create Date: 2026-07-24 01:09:01.407245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5660b2f90ea8'
down_revision: Union[str, Sequence[str], None] = '5854003476ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('message_citations', 'form',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.String(length=64),
               existing_nullable=False)
    op.alter_column('source_documents', 'form',
               existing_type=sa.VARCHAR(length=16),
               type_=sa.String(length=64),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('source_documents', 'form',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=16),
               existing_nullable=False)
    op.alter_column('message_citations', 'form',
               existing_type=sa.String(length=64),
               type_=sa.VARCHAR(length=16),
               existing_nullable=False)
