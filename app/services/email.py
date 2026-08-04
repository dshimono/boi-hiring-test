import resend
import structlog
from resend.http_client_httpx import HTTPXClient

from app.core.config import settings

logger = structlog.get_logger(__name__)

resend.api_key = settings.resend_api_key
# Default is 30s and unset by us; bound it explicitly and use the SDK's native
# async client so the send no longer needs a threadpool hop to stay non-blocking.
resend.default_async_http_client = HTTPXClient(timeout=settings.resend_timeout_seconds)


class EmailService:
    """Thin wrapper around Resend for sending transactional email."""

    async def send_magic_link(self, *, to: str, magic_link_url: str) -> None:
        """Email the sign-in link, or log it if no RESEND_API_KEY is configured."""
        if not settings.resend_api_key:
            logger.info(
                "Skipped sending magic-link email: RESEND_API_KEY not set.",
                to=to,
                magic_link_url=magic_link_url,
            )
            return

        await resend.Emails.send_async(
            {
                "from": settings.email_from,
                "to": to,
                "subject": "Your sign-in link",
                "html": (
                    "<p>Click the link below to sign in:</p>"
                    f'<p><a href="{magic_link_url}">{magic_link_url}</a></p>'
                    f"<p>This link expires in {settings.magic_link_expire_minutes} minutes.</p>"
                ),
            },
        )
