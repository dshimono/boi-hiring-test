"""seed auth bypass user

Revision ID: c35f7187a9e8
Revises: 0ffe8a69dbe8
Create Date: 2026-08-02 16:39:21.734909

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c35f7187a9e8"
down_revision: str | Sequence[str] | None = "0ffe8a69dbe8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BYPASS_USER_ID = "019fc320-ff07-7de1-8dc2-7a66689cc8c5"
BYPASS_USER_EMAIL = "bypass@example.com"

users_table = sa.table(
    "users",
    sa.column("id", sa.Uuid()),
    sa.column("email", sa.String()),
    sa.column("is_active", sa.Boolean()),
    sa.column("is_verified", sa.Boolean()),
)


def upgrade() -> None:
    """Upgrade schema."""
    insert_stmt = postgresql.insert(users_table).values(
        id=BYPASS_USER_ID,
        email=BYPASS_USER_EMAIL,
        is_active=True,
        is_verified=True,
    )
    op.execute(insert_stmt.on_conflict_do_nothing(index_elements=["email"]))


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(users_table.delete().where(users_table.c.id == BYPASS_USER_ID))
