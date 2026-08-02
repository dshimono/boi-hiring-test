from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import MagicLinkRequest, MagicLinkRequestResponse, MagicLinkVerify, Token
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/magic-link", response_model=MagicLinkRequestResponse)
async def request_magic_link(
    payload: MagicLinkRequest, db: AsyncSession = Depends(get_db)
) -> MagicLinkRequestResponse:
    """Request a sign-in link be emailed to the given address."""
    await AuthService(db).request_magic_link(payload.email)
    return MagicLinkRequestResponse()


@router.post("/verify", response_model=Token)
async def verify_magic_link(payload: MagicLinkVerify, db: AsyncSession = Depends(get_db)) -> Token:
    """Redeem a magic link token for a JWT access token."""
    return await AuthService(db).verify_magic_link(payload.token)
