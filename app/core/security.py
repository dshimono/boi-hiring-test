import secrets


def generate_token(n_bytes: int = 32) -> str:
    return secrets.token_urlsafe(n_bytes)
