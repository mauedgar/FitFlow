"""Redis dependency behavior without importing a configured client eagerly."""

import pytest

from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.services.errors import ExternalServiceError


def test_redis_client_is_deferred_until_an_operation_requires_it() -> None:
    original_url = settings.REDIS_URL
    try:
        settings.REDIS_URL = None
        with pytest.raises(ExternalServiceError, match="no está configurado"):
            get_redis_client()
    finally:
        settings.REDIS_URL = original_url
