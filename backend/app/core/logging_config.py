import logging

from app.core.config import settings


def configure_logging() -> None:
    level = logging.DEBUG if not settings.is_production else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    # uvicorn's own loggers already cover access/error lines at a sane
    # level; just make sure they inherit the same format/level instead of
    # defaulting to their own configuration.
    for noisy_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(noisy_logger).setLevel(level)

    # pymongo's own DEBUG output includes full topology/connection details
    # on every heartbeat — noisy and not something app-level DEBUG should
    # imply. Keep it at WARNING regardless of environment.
    logging.getLogger("pymongo").setLevel(logging.WARNING)
