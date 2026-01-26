from unittest.mock import patch
from models import Booking
from services.watchdog_service import mark_disrupted
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