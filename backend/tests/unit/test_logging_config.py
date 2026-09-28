"""Operational logging configuration contract."""

import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging_config import configure_logging


def test_log_level_is_normalized_and_applied() -> None:
    configured = Settings(
        _env_file=None,  # type: ignore[reportCallIssue]
        DATABASE_URL="postgresql://fitflow:secret@localhost/fitflow_test",
        SECRET_KEY="test-only",
        LOG_LEVEL="debug",
    )
    logger_names = (None, "uvicorn", "uvicorn.error", "uvicorn.access")
    original_levels = [logging.getLogger(name).level for name in logger_names]

    try:
        configure_logging(configured.LOG_LEVEL)
        assert all(logging.getLogger(name).level == logging.DEBUG for name in logger_names)
    finally:
        for name, level in zip(logger_names, original_levels, strict=True):
            logging.getLogger(name).setLevel(level)


def test_invalid_log_level_fails_configuration() -> None:
    with pytest.raises(ValidationError, match="LOG_LEVEL must be"):
        Settings(
            _env_file=None,  # type: ignore[reportCallIssue]
            DATABASE_URL="postgresql://fitflow:secret@localhost/fitflow_test",
            SECRET_KEY="test-only",
            LOG_LEVEL="verbose",
        )
