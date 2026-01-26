import pytest
from datetime import date
from services.watchdog_service import overlaps, match_event_to_bookings
from types import SimpleNamespace

def test_date_overlaps_logic():
    booking = SimpleNamespace(start_date=date(2026, 5, 1), end_date=date(2026, 5, 10))
    event_from = date(2026, 5, 5)
    event_to = date(2026, 5, 15)
    assert overlaps(booking, event_from, event_to) is True

def test_match_event_to_hotel_booking():
    event = {
        "type": "HOTEL",
        "hotel_id": 10,
        "date_from": "2026-05-01",
        "date_to": "2026-05-10",
        "message": "Awaria"
    }
    booking = SimpleNamespace(status="booked", hotel_id=10, start_date=date(2026, 5, 1), end_date=date(2026, 5, 10))
    affected = match_event_to_bookings(event, [booking])
    assert len(affected) == 1

def test_watchdog_ignores_different_city():
    event = {"type": "WEATHER", "city": "Rzym", "date_from": "2026-05-01", "date_to": "2026-05-10"}
    booking = SimpleNamespace(status="booked", visited_city=SimpleNamespace(name="Paryż"), 
                              start_date=date(2026, 5, 2), end_date=date(2026, 5, 8))
    
    affected = match_event_to_bookings(event, [booking])
    assert len(affected) == 0 


def test_match_event_wrong_date():
    event = {
        "type": "FLIGHT",
        "flight_id": 10,
        "date_from": "2026-05-15",
        "date_to": "2026-05-15",
        "severity": "HIGH",
        "message": "Lot odwołany"
    }
    
    booking = SimpleNamespace(
        status="booked",
        start_flight_id=10, 
        end_flight_id=99,
        start_date=date(2026, 5, 16), 
        end_date=date(2026, 5, 20)
    )
    
    affected = match_event_to_bookings(event, [booking])
    
    assert len(affected) == 0      