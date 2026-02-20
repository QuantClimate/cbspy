import httpx
import pytest


@pytest.fixture
def http_client():
    """A real httpx client for building OData instances in tests."""
    return httpx.Client()
