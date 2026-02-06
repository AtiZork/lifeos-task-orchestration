"""Pytest configuration and fixtures."""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    """Set async backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
