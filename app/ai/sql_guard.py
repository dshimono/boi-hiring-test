"""Safety guardrails for the run_sql_query AI tool.

This is the app-level layer: a real parsed SQL AST (not string/regex matching,
which is well known to be bypassable) restricted to a single read-only SELECT
against the three ads tables. It is deliberately not the only layer — see
app/ai/tools.py, which additionally executes the query under a Postgres role
that can only SELECT these same three tables, inside a read-only transaction,
as a backstop if this validation ever has a gap.
"""

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, SqlglotError

ALLOWED_TABLES = {"ads", "ad_comments", "ad_metrics"}
BLOCKED_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "dblink",
    "dblink_exec",
    "dblink_connect",
    "set_config",
    "pg_terminate_backend",
    "pg_cancel_backend",
}
MAX_ROWS = 200
STATEMENT_TIMEOUT_S = 5
READONLY_ROLE = "ai_query_readonly"

_ALLOWED_STATEMENT_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)
_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.IGNORECASE
)


def validate_select_only(sql: str) -> exp.Query:
    """Parse `sql` and reject anything but a single safe SELECT against the
    allowed ads tables. Raises ValueError with a specific, LLM-readable
    reason on rejection so the model can self-correct."""
    try:
        parsed_statements = sqlglot.parse(sql, dialect="postgres", error_level=ErrorLevel.RAISE)
    except SqlglotError as e:
        raise ValueError(f"could not parse SQL: {e}") from None
    statements = [s for s in parsed_statements if s is not None]

    if len(statements) != 1:
        raise ValueError("only a single SELECT statement is allowed")

    parsed = statements[0]
    if not isinstance(parsed, _ALLOWED_STATEMENT_TYPES):
        raise ValueError("only SELECT statements are allowed")

    _check_tables(parsed)
    _check_columns(parsed)
    _check_functions(parsed)
    return parsed


def _check_tables(parsed: exp.Expression) -> None:
    cte_aliases = {cte.alias.lower() for cte in parsed.find_all(exp.CTE)}
    for table in parsed.find_all(exp.Table):
        name = table.name.lower()
        if name in cte_aliases:
            continue
        schema = (table.db or "").lower()
        if schema and schema != "public":
            raise ValueError(f"table '{table.db}.{table.name}' is not queryable")
        if name not in ALLOWED_TABLES:
            raise ValueError(f"table '{table.name}' is not queryable")


def _check_columns(parsed: exp.Expression) -> None:
    for select in parsed.find_all(exp.Select):
        for projection in select.expressions:
            if isinstance(projection, exp.Star):
                raise ValueError("SELECT * is not allowed — list columns explicitly")
            for column in projection.find_all(exp.Column):
                if column.name.lower() == "id":
                    raise ValueError("column 'id' is not queryable")


def _check_functions(parsed: exp.Expression) -> None:
    for fn in parsed.find_all(exp.Anonymous):
        if fn.name.lower() in BLOCKED_FUNCTIONS:
            raise ValueError(f"function '{fn.name}' is not allowed")


def apply_row_cap(parsed: exp.Query, max_rows: int = MAX_ROWS) -> exp.Query:
    """Cap the query's LIMIT at max_rows, leaving a smaller explicit LIMIT as-is."""
    existing = parsed.args.get("limit")
    if existing is not None:
        try:
            if int(existing.expression.this) <= max_rows:
                return parsed
        except (AttributeError, TypeError, ValueError):
            pass
    return parsed.limit(max_rows)


def scrub_uuids(rows: list[dict]) -> list[dict]:
    """Drop the 'id' column and redact any UUID-shaped value, so a row's
    primary key can never reach the model — whether by column name (aliasing
    can't dodge this, we drop the *source* column during validation) or by
    value hiding in a cast/expression under a different key."""
    scrubbed = []
    for row in rows:
        clean = {}
        for key, value in row.items():
            if key.lower() == "id":
                continue
            if isinstance(value, str) and _UUID_RE.search(value):
                clean[key] = "[redacted]"
            else:
                clean[key] = value
        scrubbed.append(clean)
    return scrubbed
