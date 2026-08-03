"""add creative text columns to ads

Revision ID: a41f9c2d7b3e
Revises: d08d87ece5ef
Create Date: 2026-08-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a41f9c2d7b3e"
down_revision: str | Sequence[str] | None = "d08d87ece5ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("ads", sa.Column("ocr_headline", sa.Text(), nullable=True))
    op.add_column("ads", sa.Column("ocr_body", sa.Text(), nullable=True))
    op.add_column("ads", sa.Column("ocr_cta", sa.Text(), nullable=True))
    op.add_column("ads", sa.Column("vision_description", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ads", "vision_description")
    op.drop_column("ads", "ocr_cta")
    op.drop_column("ads", "ocr_body")
    op.drop_column("ads", "ocr_headline")
