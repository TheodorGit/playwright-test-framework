"""The booking API: its contract, its refusals, and one booking's whole life."""

import httpx
import pytest
from jsonschema import validate

from .schemas import BOOKING_SCHEMA, CREATED_BOOKING_SCHEMA

pytestmark = pytest.mark.api

BAD_CREDENTIALS = {"username": "admin", "password": "definitely-wrong"}
MISSING_ID = 999999999
DELETED = 201


def _assert_status(response: httpx.Response, wanted: int):
    body = (response.text or "")[:200]
    assert response.status_code == wanted, (
        f"{response.request.method} {response.request.url.path} answered "
        f"{response.status_code}, not {wanted}: {body}")
    return response.status_code


def _assert_fields(found: dict, wanted: dict):
    differing = {key: (value, found.get(key)) for key, value in wanted.items()
                 if found.get(key) != value}
    assert not differing, f"(sent, returned) differ: {differing}"
    return len(wanted)


def test_created_booking_matches_the_contract(api_client, booking_payload, checks):
    response = api_client.post("/booking", json=booking_payload)
    body = response.json() if response.content else {}

    checks.check("the API accepts the booking",
                 lambda: _assert_status(response, 200),
                 expected="200, the documented success code")
    checks.check("the response honours the documented contract",
                 lambda: validate(instance=body, schema=CREATED_BOOKING_SCHEMA),
                 expected="a bookingid and a booking, with the documented types")
    checks.check("the booking it echoes back is the booking sent",
                 lambda: _assert_fields(body.get("booking", {}), booking_payload),
                 expected="every field as sent, nothing silently changed",
                 found=lambda count: f"{count} fields returned unchanged")
    checks.tally("bookings created", 1)


def test_read_booking_matches_the_contract(api_client, booking_payload, checks):
    created = api_client.post("/booking", json=booking_payload)
    booking_id = created.json()["bookingid"]
    response = api_client.get(f"/booking/{booking_id}")
    body = response.json() if response.content else {}

    checks.check("the booking can be read back by its id",
                 lambda: _assert_status(response, 200),
                 expected=f"200 for booking {booking_id}")
    checks.check("the booking read back honours the documented contract",
                 lambda: validate(instance=body, schema=BOOKING_SCHEMA),
                 expected="the documented booking fields and types")
    checks.check("it holds what was created, not a default",
                 lambda: _assert_fields(body, booking_payload),
                 expected="the same name, price, deposit and dates",
                 found=lambda count: f"{count} fields match the creation")
    checks.tally("bookings created", 1)


def test_auth_refuses_wrong_credentials(api_client, checks):
    response = api_client.post("/auth", json=BAD_CREDENTIALS)
    body = response.json() if response.content else {}

    checks.check("the request itself is answered",
                 lambda: _assert_status(response, 200),
                 expected="200, since this API reports auth failures in the body")
    checks.check("no token is issued",
                 lambda: _assert_no_token(body),
                 expected="a body with no token in it")
    checks.check("the refusal says why",
                 lambda: _assert_reason(body, "Bad credentials"),
                 expected="reason: Bad credentials")


def test_missing_booking_returns_404(api_client, checks):
    response = api_client.get(f"/booking/{MISSING_ID}")

    checks.check("a booking that does not exist answers 404",
                 lambda: _assert_status(response, 404),
                 expected=f"404 for booking {MISSING_ID}, not an empty 200")


def test_booking_lifecycle(api_client, auth_token, booking_payload, checks):
    """Create, update, read back and delete, each stage its own check."""
    created = api_client.post("/booking", json=booking_payload)
    checks.check("the booking is created",
                 lambda: _assert_status(created, 200),
                 expected="200 with a new bookingid")
    booking_id = created.json()["bookingid"]
    checks.add_metadata("booking_id", booking_id)
    checks.tally("bookings created", 1)

    # This API authorises writes with a token in a cookie.
    headers = {"Cookie": f"token={auth_token}"}
    updated_payload = {**booking_payload, "totalprice": 999}
    updated = api_client.put(f"/booking/{booking_id}", json=updated_payload,
                             headers=headers)
    checks.check("the update is accepted",
                 lambda: _assert_status(updated, 200),
                 expected="200 for the authorised update")

    fetched = api_client.get(f"/booking/{booking_id}")
    checks.check("the update is what the API now reports",
                 lambda: _assert_fields(fetched.json(), {"totalprice": 999}),
                 expected="totalprice 999, read back from the API")

    deleted = api_client.delete(f"/booking/{booking_id}", headers=headers)
    checks.check("the booking is deleted",
                 lambda: _assert_status(deleted, DELETED),
                 expected=f"{DELETED}, this API's documented delete code")

    gone = api_client.get(f"/booking/{booking_id}")
    checks.check("the deleted booking is gone, not merely hidden",
                 lambda: _assert_status(gone, 404),
                 expected="404 once it is deleted")


def _assert_no_token(body: dict):
    assert "token" not in body, f"a token was issued for wrong credentials: {body}"


def _assert_reason(body: dict, wanted: str):
    found = body.get("reason")
    assert found == wanted, f"the refusal says {found}, expected {wanted}"
