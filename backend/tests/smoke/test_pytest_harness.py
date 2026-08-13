import sys

import pytest


@pytest.mark.smoke
def test_pytest_harness_uses_supported_python_runtime() -> None:
    """Minimal harness check; domain coverage is added by FF-LOCAL-001."""
    assert sys.version_info >= (3, 11)
