import pytest

from app.core.config import Settings


def test_auth_disabled_requires_bypass_user_id() -> None:
    with pytest.raises(ValueError, match="AUTH_BYPASS_USER_ID"):
        Settings(secret_key="test-secret", auth_enabled=False)
