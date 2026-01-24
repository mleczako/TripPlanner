import pytest
from services.booking_state_machine import get_next_booking_status
from services.payment_validator import validate_payment_details

def test_status_transition_to_pending():
    new_status = get_next_booking_status("prepared", "start_payment")
    assert new_status == "pending"

def test_status_transition_success():

    new_status = get_next_booking_status("pending", "payment_success")
    assert new_status == "booked"

def test_status_transition_cancel():

    new_status = get_next_booking_status("booked", "cancel")
    assert new_status == "canceled"


def test_payment_blik_valid():
    assert validate_payment_details("blik", "123456") is None

def test_payment_blik_invalid():
    msg = validate_payment_details("blik", "123")
    assert "Nieprawidłowy kod BLIK" in msg

def test_payment_card_invalid():
    msg = validate_payment_details("card", "123")
    assert "Numer karty jest za krótki" in msg