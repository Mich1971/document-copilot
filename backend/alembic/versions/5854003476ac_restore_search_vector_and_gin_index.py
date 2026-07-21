"""restore_search_vector_and_gin_index

Revision ID: 5854003476ac
Revises: 195ca4715531
Create Date: 2026-07-20 22:20:02.659879

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '5854003476ac'
down_revision: Union[str, Sequence[str], None] = '195ca4715531'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        text(
            "ALTER TABLE document_chunks "
            "ADD COLUMN search_vector tsvector "
            "GENERATED ALWAYS AS (to_tsvector('spanish', COALESCE(text, '') || ' ' || COALESCE(section, ''))) STORED"
        )
    )
    op.execute(
        text(
            "CREATE INDEX ix_document_chunks_search_vector_gin "
            "ON document_chunks USING gin (search_vector)"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(text("DROP INDEX IF EXISTS ix_document_chunks_search_vector_gin"))
    op.execute(text("ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector"))
