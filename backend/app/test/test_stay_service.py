import pytest
from datetime import date
from types import SimpleNamespace
from services.stay_service import get_total_saved_price, get_stays_number

def test_get_total_saved_price_mixed_bookings():
    bookings = [
        SimpleNamespace(total_price=800.0, status="booked", discount=20.0),
        SimpleNamespace(total_price=500.0, status="completed", discount=0.0),
        SimpleNamespace(total_price=1000.0, status="canceled", discount=50.0),
        SimpleNamespace(total_price=300.0, status="booked", discount=None)
    ]
    
    spent, saved = get_total_saved_price(bookings)
    
    assert spent == 1600.0
    assert saved == 200.0

def test_get_total_saved_price_all_canceled():
    bookings = [
        SimpleNamespace(total_price=1000.0, status="canceled", discount=10.0)
    ]
    spent, saved = get_total_saved_price(bookings)
    assert spent == 0
    assert saved == 0

def test_get_total_saved_price_empty_list():
    assert get_total_saved_price([]) == (0, 0)


def test_get_stays_number_logic():
    today = date(2026, 1, 22)
    
    bookings = [
        SimpleNamespace(start_date=date(2026, 2, 1), status="booked"),
        SimpleNamespace(start_date=date(2026, 1, 10), status="completed"),
        SimpleNamespace(start_date=date(2026, 3, 1), status="canceled"),
        SimpleNamespace(start_date=date(2026, 1, 22), status="booked"),
        SimpleNamespace(start_date=date(2026, 5, 1), status="disrupted")
    ]
    
    total, upcoming = get_stays_number(bookings, today)
    
    assert total == 4
    assert upcoming == 2

def test_get_stays_number_no_upcoming():
    today = date(2026, 1, 22)
    bookings = [
        SimpleNamespace(start_date=date(2025, 12, 1), status="completed"),
        SimpleNamespace(start_date=date(2026, 1, 1), status="booked")
    ]
    total, upcoming = get_stays_number(bookings, today)
    assert total == 2
    assert upcoming == 0