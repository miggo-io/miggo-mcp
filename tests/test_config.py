import pytest

from miggo_public_server.config import (
    ConfigurationError,
    DEFAULT_API_URL,
    DEFAULT_PAGE_SIZE,
    PublicServerSettings,
)


def test_from_env_uses_defaults_and_strips_slash():
    settings = PublicServerSettings.from_env(
        {
            "MIGGO_PUBLIC_TOKEN": "secret-token",
            "MIGGO_PUBLIC_API_URL": "https://example.com/",
        }
    )

    assert settings.api_url == "https://example.com"
    assert settings.token == "secret-token"
    assert settings.default_take == DEFAULT_PAGE_SIZE
    assert settings.default_skip == 0
    assert settings.default_sort == "risk,desc"


def test_from_env_without_overrides():
    settings = PublicServerSettings.from_env({"MIGGO_PUBLIC_TOKEN": "abc"})

    assert settings.api_url == DEFAULT_API_URL
    assert settings.default_take == DEFAULT_PAGE_SIZE
    assert settings.default_skip == 0


@pytest.mark.parametrize(
    "env",
    [
        {"MIGGO_PUBLIC_TOKEN": "abc", "MIGGO_PUBLIC_DEFAULT_SORT": "name"},
        {"MIGGO_PUBLIC_TOKEN": "abc", "MIGGO_PUBLIC_DEFAULT_SORT": "name,sideways"},
    ],
)
def test_invalid_default_sort(env):
    with pytest.raises(ConfigurationError):
        PublicServerSettings.from_env(env)


def test_default_take_bounds():
    with pytest.raises(ConfigurationError):
        PublicServerSettings.from_env(
            {"MIGGO_PUBLIC_TOKEN": "abc", "MIGGO_PUBLIC_DEFAULT_TAKE": "100"}
        )
