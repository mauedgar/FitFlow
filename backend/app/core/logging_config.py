"""Minimal process logging configuration driven by application settings."""

import logging


def configure_logging(level_name: str) -> None:
    """Apply one validated level to application and Uvicorn loggers."""
    level = logging.getLevelNamesMapping()[level_name]
    logging.getLogger().setLevel(level)
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).setLevel(level)
