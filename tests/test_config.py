import pytest
from pydantic import ValidationError

from miggo_mcp.config import (
    DEFAULT_API_URL,
    DEFAULT_PAGE_SIZE,
    PublicServerSettings,
)
from miggo_mcp.constants import MAX_PAGE_SIZE


def test_settings_use_defaults_and_strip_slash():
    settings = PublicServerSettings.model_validate(
        {
            "api_url": "https://example.com/",
            "token": "secret-token",
        }
    )

    assert settings.api_url == "https://example.com"
    assert settings.token == "secret-token"
    assert settings.default_take == DEFAULT_PAGE_SIZE
    assert settings.default_skip == 0
    assert settings.default_sort == "risk,desc"


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MIGGO_PUBLIC_TOKEN", "env-token")
    monkeypatch.setenv("MIGGO_PUBLIC_API_URL", "https://env.example.com/")

    settings = PublicServerSettings()

    assert settings.token == "env-token"
    assert settings.api_url == "https://env.example.com"
    assert settings.default_take == DEFAULT_PAGE_SIZE
    assert settings.default_skip == 0


def test_model_defaults_without_overrides():
    settings = PublicServerSettings.model_validate({"token": "abc"})

    assert settings.api_url == DEFAULT_API_URL
    assert settings.default_take == DEFAULT_PAGE_SIZE
    assert settings.default_skip == 0


@pytest.mark.parametrize(
    "data",
    [
        {"token": "abc", "default_sort": "name"},
        {"token": "abc", "default_sort": "name,sideways"},
    ],
)
def test_invalid_default_sort(data):
    with pytest.raises(ValidationError):
        PublicServerSettings.model_validate(data)


def test_default_take_bounds():
    with pytest.raises(ValidationError):
        PublicServerSettings.model_validate(
            {"token": "abc", "default_take": MAX_PAGE_SIZE + 1}
        )
