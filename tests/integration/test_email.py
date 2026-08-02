"""Sends a real email through Resend — no mocking.

Skipped until RESEND_API_KEY is set in .env. Once it's set, a failure here
surfaces Resend's own error (invalid key, unverified EMAIL_FROM domain, etc.)
directly, so .env can be iterated on until this passes.

Sends to `delivered@resend.dev`, Resend's test address that's accepted and
marked delivered without reaching a real inbox — safe to run repeatedly.
https://resend.com/docs/dashboard/emails/send-test-emails
"""

import pytest

from app.core.config import settings
from app.services.email import EmailService

RESEND_TEST_RECIPIENT = "delivered@resend.dev"


@pytest.mark.real_email
@pytest.mark.skipif(not settings.resend_api_key, reason="RESEND_API_KEY not configured in .env")
@pytest.mark.asyncio
async def test_send_magic_link_via_resend() -> None:
    await EmailService().send_magic_link(
        to=RESEND_TEST_RECIPIENT,
        magic_link_url="http://localhost:8000/auth/verify?token=integration-test-token",
    )
