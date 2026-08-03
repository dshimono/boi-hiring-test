import pytest

from app.ai.sql_guard import (
    MAX_ROWS,
    apply_row_cap,
    scrub_uuids,
    validate_select_only,
)


def test_accepts_simple_allowed_select() -> None:
    parsed = validate_select_only("SELECT ad_id, impressions FROM ad_metrics")
    assert parsed.sql(dialect="postgres") == "SELECT ad_id, impressions FROM ad_metrics"


def test_accepts_join_across_allowed_tables() -> None:
    validate_select_only(
        "SELECT a.ad_id, m.impressions FROM ads a JOIN ad_metrics m ON a.ad_id = m.ad_id"
    )


def test_accepts_count_star() -> None:
    validate_select_only("SELECT ad_id, COUNT(*) FROM ad_comments GROUP BY ad_id")


def test_accepts_cte_referencing_only_allowed_tables() -> None:
    validate_select_only("WITH recent AS (SELECT ad_id FROM ads) SELECT ad_id FROM recent")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO ads (ad_id) VALUES ('x')",
        "UPDATE ads SET title = 'x'",
        "DELETE FROM ads",
        "DROP TABLE ads",
        "CREATE TABLE evil (id int)",
        "ALTER TABLE ads ADD COLUMN evil text",
        "EXPLAIN SELECT * FROM ads",
    ],
)
def test_rejects_non_select_statements(sql: str) -> None:
    with pytest.raises(ValueError):
        validate_select_only(sql)


def test_rejects_stacked_statements() -> None:
    with pytest.raises(ValueError, match="single"):
        validate_select_only("SELECT ad_id FROM ads; DROP TABLE ads;")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM users",
        "SELECT * FROM magic_links",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM pg_catalog.pg_tables",
    ],
)
def test_rejects_disallowed_tables(sql: str) -> None:
    with pytest.raises(ValueError, match="not queryable"):
        validate_select_only(sql)


def test_rejects_bare_star_projection() -> None:
    with pytest.raises(ValueError, match=r"\*"):
        validate_select_only("SELECT * FROM ads")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT id FROM ads",
        "SELECT id AS foo FROM ads",
        "SELECT a.id FROM ads a",
        "SELECT id::text FROM ads",
    ],
)
def test_rejects_id_column_regardless_of_alias_or_cast(sql: str) -> None:
    with pytest.raises(ValueError, match="id"):
        validate_select_only(sql)


def test_rejects_blocked_function_call() -> None:
    with pytest.raises(ValueError, match="pg_sleep"):
        validate_select_only("SELECT pg_sleep(5) FROM ads")


def test_rejects_unparseable_sql() -> None:
    with pytest.raises(ValueError):
        validate_select_only("SELECT ((( FROM ads")


def test_apply_row_cap_adds_limit_when_absent() -> None:
    parsed = validate_select_only("SELECT ad_id FROM ads")
    capped = apply_row_cap(parsed)
    assert f"LIMIT {MAX_ROWS}" in capped.sql(dialect="postgres")


def test_apply_row_cap_clamps_large_limit() -> None:
    parsed = validate_select_only("SELECT ad_id FROM ads LIMIT 100000")
    capped = apply_row_cap(parsed)
    assert f"LIMIT {MAX_ROWS}" in capped.sql(dialect="postgres")


def test_apply_row_cap_leaves_smaller_limit_untouched() -> None:
    parsed = validate_select_only("SELECT ad_id FROM ads LIMIT 5")
    capped = apply_row_cap(parsed)
    assert "LIMIT 5" in capped.sql(dialect="postgres")


def test_scrub_uuids_drops_id_column() -> None:
    rows = [{"id": "0199a1b2-1234-7abc-8def-0123456789ab", "ad_id": "ad_1"}]
    assert scrub_uuids(rows) == [{"ad_id": "ad_1"}]


def test_scrub_uuids_redacts_uuid_shaped_value_under_other_key() -> None:
    rows = [{"note": "see 0199a1b2-1234-7abc-8def-0123456789ab for details"}]
    assert scrub_uuids(rows) == [{"note": "[redacted]"}]


def test_scrub_uuids_leaves_non_uuid_values_alone() -> None:
    rows = [{"ad_id": "ad_1", "impressions": 1000}]
    assert scrub_uuids(rows) == [{"ad_id": "ad_1", "impressions": 1000}]
