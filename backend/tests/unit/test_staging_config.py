"""Configuration contract for staging without weakening development or tests."""

import pytest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import app


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "_env_file": None,
        "ENV": "staging",
        "DEBUG": False,
        "DATABASE_URL": "postgresql://fitflow:secret@postgres:5432/fitflow",
        "SECRET_KEY": "injected-at-runtime",
        "REDIS_URL": "redis://redis:6379/0",
        "BACKEND_CORS_ORIGINS": ["https://staging.fitflow.example"],
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("profile", "debug", "testing"),
    [("development", True, False), ("test", False, True)],
)
def test_existing_profiles_preserve_optional_redis_and_local_cors(
    profile: str,
    debug: bool,
    testing: bool,
) -> None:
    configured = make_settings(
        ENV=profile,
        DEBUG=debug,
        TESTING=testing,
        REDIS_URL=None,
        BACKEND_CORS_ORIGINS=["http://localhost:5173"],
    )

    assert configured.REDIS_URL is None
    assert configured.BACKEND_CORS_ORIGINS == ["http://localhost:5173"]


def test_staging_accepts_explicit_non_development_configuration() -> None:
    configured = make_settings()

    assert configured.ENV == "staging"
    assert configured.DEBUG is False


def test_application_uses_configured_cors_origins() -> None:
    cors = next(middleware for middleware in app.user_middleware if middleware.cls is CORSMiddleware)

    assert cors.kwargs["allow_origins"] == settings.BACKEND_CORS_ORIGINS


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"DEBUG": True}, "DEBUG must be false"),
        ({"REDIS_URL": None}, "REDIS_URL is required"),
        ({"BACKEND_CORS_ORIGINS": []}, "BACKEND_CORS_ORIGINS is required"),
        (
            {"BACKEND_CORS_ORIGINS": ["http://localhost:5173"]},
            "localhost CORS origins are forbidden",
        ),
    ],
)
def test_staging_fails_closed_on_unsafe_or_missing_values(
    override: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        make_settings(**override)
