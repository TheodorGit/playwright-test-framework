"""Fixtures for the API test layer (restful-booker)."""

import httpx
import pytest

from config import settings

# Public, documented sandbox credentials for restful-booker's auth
# endpoint — not secrets.
SANDBOX_ADMIN = {"username": "admin", "password": "password123"}


@pytest.fixture(scope="session")
def api_client():
    """Session-scoped HTTP client bound to the API under test."""
    with httpx.Client(
        base_url=settings.api_base_url,
        timeout=30.0,
        headers={"Accept": "application/json"},
    ) as client:
        yield client


@pytest.fixture(scope="session")
def auth_token(api_client: httpx.Client) -> str:
    """Authenticate once per session and return the API token."""
    response = api_client.post("/auth", json=SANDBOX_ADMIN)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    token = response.json().get("token")
    assert token, f"No token in auth response: {response.text}"
    return token


@pytest.fixture
def booking_payload() -> dict:
    """A valid booking creation payload."""
    return {
        "firstname": "Ada",
        "lastname": "Lovelace",
        "totalprice": 250,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-05"},
        "additionalneeds": "Late checkout",
    }
