"""
Pytest configuration and test fixtures for InsureChain VoiceGuard backend.
Uses httpx.AsyncClient for non-blocking API tests.
"""

import sys
from typing import AsyncGenerator

# Ensure Windows asyncio compatibility with psycopg 3 in tests
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx
import pytest
from app.main import app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Yields an AsyncClient bound to the FastAPI application via ASGITransport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
