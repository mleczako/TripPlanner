from unittest.mock import patch
from models import Booking, City, Hotel
from datetime import date
from services.watchdog_service import mark_disrupted
import pytest

@pytest.fixture
def setup_search_data(db_session):
    ny = City(id=2, name="Nowy Jork")
    wa = City(id=1, name="Warszawa")
    
    db_session.add(ny)
    db_session.add(wa)
    
    plaza = Hotel(
        id=10,
        name="Plaza Hotel",
        address="Fifth Avenue, NY",
        city_id=2,
        rating=5.0,
        price=915.0, 
        capacity=2,
        has_wifi=True,
        has_pool=True,
        start_date=date(2027, 6, 1),
        end_date=date(2027, 6, 30)
    )
    db_session.add(plaza)
    
    booking = Booking(
        id=500,
        status="prepared", 
        start_city_id=1,  
        visited_city_id=2, 
        hotel_id=10,
        total_price=9150.0,
        guests=2,
        rating=5.0,
        start_date=date(2027, 6, 1),
        end_date=date(2027, 6, 7),
        start_flight_id=101,
        end_flight_id=102
    )
    db_session.add(booking)
    
    db_session.commit()
    return {"ny": ny, "wa": wa, "hotel": plaza, "booking": booking}
def test_system_e2e_full_repair_flow(client, db_session, setup_search_data):
    original = db_session.get(Booking, 500)
    
    disruption = {"type": "HOTEL", "hotel_id": 10, "date_from": "2027-06-01", 
                  "date_to": "2027-06-07", "severity": "HIGH", "message": "Awaria"}
    
    mark_disrupted(db_session, original, disruption)
    db_session.commit()

    with patch("services.alternative_service.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [{
                "id": 20,
                "name": "Alternative Hotel",
                "address": "ul. Testowa 1, Nowy Jork",
                "price_per_night": 400.0,
                "rating": 5.0,
                "city_id": 2,
                "capacity": 2,
                "has_wifi": True,
                "has_pool": False,     
                "has_restaurant": False 
            }]

            from services.alternative_service import create_alternatives_for_disrupted_booking
            create_alternatives_for_disrupted_booking(db_session, original)
    alt = db_session.query(Booking).filter(Booking.parent_booking_id == 500).first()
    assert alt is not None
    assert alt.status == "prepared"

    response = client.post(f"/bookings/{original.id}/accept/{alt.id}", follow_redirects=True)
    db_session.refresh(original)
    db_session.refresh(alt)
    
    assert original.status == "cancelled"
    assert alt.status == "booked"