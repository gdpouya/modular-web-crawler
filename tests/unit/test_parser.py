"""Test URL normalization."""
import pytest
from app.parser import normalize_url


@pytest.mark.parametrize("input_url,expected", [
    # Basic normalization
    (
        "HTTP://Example.COM/Path",
        "http://example.com/Path",
    ),
    # Remove default ports
    (
        "http://example.com:80/path",
        "http://example.com/path",
    ),
    (
        "https://example.com:443/path",
        "https://example.com/path",
    ),
    # Sort query parameters
    (
        "http://example.com/path?b=2&a=1",
        "http://example.com/path?a=1&b=2",
    ),
    # Remove fragments
    (
        "http://example.com/path#section",
        "http://example.com/path",
    ),
    # Remove trailing slash for non-root
    (
        "http://example.com/path/",
        "http://example.com/path",
    ),
    # Keep root slash
    (
        "http://example.com/",
        "http://example.com/",
    ),
])
def test_normalize_url(input_url, expected):
    assert normalize_url(input_url) == expected