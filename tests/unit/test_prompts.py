from datetime import date

from app.ai.prompts import build_system_prompt


def test_build_system_prompt_includes_resolved_date_range() -> None:
    prompt = build_system_prompt(date(2025, 6, 30), date(2025, 8, 15))

    assert "2025-06-30 to 2025-08-15" in prompt
    assert "get_ad_performance" in prompt


def test_build_system_prompt_handles_no_data() -> None:
    prompt = build_system_prompt(None, None)

    assert "no data loaded yet" in prompt
