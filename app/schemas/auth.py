from pydantic import BaseModel, EmailStr


class MagicLinkRequest(BaseModel):
    """Body for requesting a magic link."""

    email: EmailStr


class MagicLinkRequestResponse(BaseModel):
    """Deliberately vague response so the endpoint can't be used to enumerate emails."""

    message: str = "If an account exists for this email, a magic link has been sent."


class MagicLinkVerify(BaseModel):
    """Body for redeeming a magic link token."""

    token: str


class Token(BaseModel):
    """A JWT access token returned after successful verification."""

    access_token: str
    token_type: str = "bearer"
