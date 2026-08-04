import logging
import sys

import structlog
from structlog.typing import Processor

from app.core.config import settings

_UVICORN_LOGGERS = ("uvicorn", "uvicorn.error")


def configure_logging() -> None:
    """Route app, sqlalchemy, alembic, and uvicorn logs through one structlog-formatted handler."""
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer = (
        structlog.processors.JSONRenderer()
        if settings.environment == "production"
        else structlog.dev.ConsoleRenderer()
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.log_level)

    # uvicorn ships its own handlers/formatters; strip them so every log line
    # (app, sqlalchemy, alembic, uvicorn) flows through the single formatter above.
    # Routine INFO chatter (startup/shutdown) duplicates what app.main's lifespan
    # already logs, so only let uvicorn's own warnings/errors through.
    for name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(logging.WARNING)

    # Access logs are emitted by our own request-logging middleware instead,
    # with structured fields (method, path, status_code, duration_ms).
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.propagate = False
