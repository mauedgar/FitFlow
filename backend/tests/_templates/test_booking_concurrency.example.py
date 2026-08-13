"""Template only: concurrency tests must exercise the real transaction boundary."""

import pytest


@pytest.mark.concurrency
@pytest.mark.asyncio
async def test_booking_does_not_overbook_under_concurrency() -> None:
    raise NotImplementedError("Template: adapt before collecting with pytest")
