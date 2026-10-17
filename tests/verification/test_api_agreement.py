"""The API checked against itself: the list and the detail view must agree."""

import pytest

pytestmark = [pytest.mark.verification, pytest.mark.api]


def test_api_list_and_detail_agree(api_client, booking_payload, steps):
    created = api_client.post("/booking", json=booking_payload)
    assert created.status_code == 200, f"could not create a booking: {created.text}"
    booking_id = created.json()["bookingid"]
    steps.add_metadata("booking_id", booking_id)
    steps.tally("bookings created", 1)

    listing = api_client.get("/booking")
    ids = [entry.get("bookingid") for entry in listing.json()] \
        if listing.status_code == 200 else []

    steps.step("the booking the run made is in the list",
               lambda: _assert_listed(ids, booking_id),
               expected=f"booking {booking_id} among the ids the list returns")
    steps.step("the list names it once, not twice",
               lambda: _assert_once(ids, booking_id),
               expected="exactly one entry for this booking")
    steps.step("the detail view holds what the run sent",
               lambda: _assert_detail(api_client, booking_id, booking_payload),
               expected="the same name, price, deposit and dates as created",
               found=lambda count: f"{count} fields agree with the creation")


def _assert_listed(ids: list, booking_id: int):
    assert ids, "the list endpoint returned no bookings at all"
    assert booking_id in ids, (
        f"booking {booking_id} was created but the list of {len(ids)} bookings "
        f"does not name it")


def _assert_once(ids: list, booking_id: int):
    found = ids.count(booking_id)
    assert found == 1, f"the list names booking {booking_id} {found} times"


def _assert_detail(api_client, booking_id: int, sent: dict) -> int:
    response = api_client.get(f"/booking/{booking_id}")
    assert response.status_code == 200, (
        f"booking {booking_id} is in the list but reading it answered "
        f"{response.status_code}")
    found = response.json()
    differing = {key: (value, found.get(key)) for key, value in sent.items()
                 if found.get(key) != value}
    assert not differing, f"(sent, returned) differ: {differing}"
    return len(sent)
