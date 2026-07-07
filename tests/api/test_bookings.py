"""
Booking API tests against restful-booker.

Demonstrates contract (schema) validation, negative testing, and a
chained CRUD workflow — five focused tests rather than exhaustive
endpoint coverage.
"""

import httpx
import pytest
from jsonschema import validate

from .schemas import BOOKING_SCHEMA, CREATED_BOOKING_SCHEMA

pytestmark = pytest.mark.api


class TestBookingContract:
    """Response-contract validation."""

    def test_created_booking_matches_schema(
        self,
        api_client: httpx.Client,
        booking_payload: dict,
    ):
        """POST /booking returns a booking that honours the documented contract."""
        response = api_client.post("/booking", json=booking_payload)

        assert response.status_code == 200
        body = response.json()
        validate(instance=body, schema=CREATED_BOOKING_SCHEMA)
        assert body["booking"] == booking_payload

    def test_get_booking_matches_schema(
        self,
        api_client: httpx.Client,
        booking_payload: dict,
    ):
        """GET /booking/{id} returns a schema-valid booking."""
        booking_id = api_client.post(
            "/booking", json=booking_payload
        ).json()["bookingid"]

        response = api_client.get(f"/booking/{booking_id}")

        assert response.status_code == 200
        validate(instance=response.json(), schema=BOOKING_SCHEMA)


class TestBookingNegative:
    """Negative-path behaviour."""

    def test_auth_rejects_bad_credentials(self, api_client: httpx.Client):
        """POST /auth with wrong credentials must not issue a token."""
        response = api_client.post(
            "/auth",
            json={"username": "admin", "password": "definitely-wrong"},
        )

        assert response.status_code == 200  # API signals failure in the body
        body = response.json()
        assert "token" not in body
        assert body.get("reason") == "Bad credentials"

    def test_get_missing_booking_returns_404(self, api_client: httpx.Client):
        """GET /booking/{id} for a non-existent id returns 404."""
        response = api_client.get("/booking/999999999")

        assert response.status_code == 404


class TestBookingWorkflow:
    """Chained CRUD workflow across multiple endpoints."""

    def test_full_booking_lifecycle(
        self,
        api_client: httpx.Client,
        auth_token: str,
        booking_payload: dict,
    ):
        """Create, update, verify and delete a booking end to end."""
        # Create
        created = api_client.post("/booking", json=booking_payload)
        assert created.status_code == 200
        booking_id = created.json()["bookingid"]

        # Update (restful-booker authorises writes via a token cookie)
        auth_headers = {"Cookie": f"token={auth_token}"}
        updated_payload = {**booking_payload, "totalprice": 999}
        updated = api_client.put(
            f"/booking/{booking_id}",
            json=updated_payload,
            headers=auth_headers,
        )
        assert updated.status_code == 200

        # Verify the update persisted
        fetched = api_client.get(f"/booking/{booking_id}")
        assert fetched.status_code == 200
        assert fetched.json()["totalprice"] == 999

        # Delete
        deleted = api_client.delete(f"/booking/{booking_id}", headers=auth_headers)
        assert deleted.status_code == 201  # restful-booker's documented success code

        # Verify it is gone
        assert api_client.get(f"/booking/{booking_id}").status_code == 404
