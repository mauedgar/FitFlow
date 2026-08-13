"""Template only: adapt fixtures and imports to the real FastAPI app."""

import pytest


@pytest.mark.api
def test_endpoint_returns_expected_contract() -> None:
    raise NotImplementedError("Template: adapt before collecting with pytest")
