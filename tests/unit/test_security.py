from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_magic_link_token,
    hash_token,
)


def test_generate_magic_link_token_is_unique() -> None:
    assert generate_magic_link_token() != generate_magic_link_token()


def test_hash_token_is_deterministic() -> None:
    token = generate_magic_link_token()
    assert hash_token(token) == hash_token(token)


def test_access_token_round_trip() -> None:
    token = create_access_token(subject="user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
