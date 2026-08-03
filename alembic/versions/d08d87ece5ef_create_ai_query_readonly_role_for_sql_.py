"""create ai_query_readonly role for sql tool

Revision ID: d08d87ece5ef
Revises: c35f7187a9e8
Create Date: 2026-08-03 17:05:06.708820

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d08d87ece5ef"
down_revision: str | Sequence[str] | None = "c35f7187a9e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# NOLOGIN: the app never connects as this role directly, it switches into it with
# SET LOCAL ROLE for the duration of one ai/run_sql_query call (see app/ai/tools.py),
# which requires membership rather than a password. Granted only SELECT on the three
# ads tables — this is the DB-enforced backstop behind that tool's app-level SQL
# validation (app/ai/sql_guard.py); it can't see users/magic_links or write anywhere,
# regardless of what SQL the model writes.
ROLE_NAME = "ai_query_readonly"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{ROLE_NAME}') THEN
                CREATE ROLE {ROLE_NAME} NOLOGIN;
            END IF;
        END
        $$;
    """)
    op.execute(f"GRANT SELECT ON ads, ad_comments, ad_metrics TO {ROLE_NAME}")
    op.execute(f"GRANT {ROLE_NAME} TO CURRENT_USER")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"REVOKE {ROLE_NAME} FROM CURRENT_USER")
    op.execute(f"REVOKE SELECT ON ads, ad_comments, ad_metrics FROM {ROLE_NAME}")
    op.execute(f"DROP ROLE IF EXISTS {ROLE_NAME}")
