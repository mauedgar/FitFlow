"""Template only: use an isolated test database/session fixture."""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_transaction_preserves_invariant() -> None:
    raise NotImplementedError("Template: adapt before collecting with pytest")
