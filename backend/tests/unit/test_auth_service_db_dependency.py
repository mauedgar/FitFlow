"""A DB session must be supplied by the FastAPI dependency lifecycle."""
from __future__ import annotations

import inspect

from app.services.auth_service import get_user_from_token


def test_auth_service_requires_managed_db_session_argument() -> None:
    parameter = inspect.signature(get_user_from_token).parameters["db"]
    assert parameter.default is inspect.Parameter.empty
    assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
