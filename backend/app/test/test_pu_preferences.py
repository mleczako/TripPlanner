from unittest.mock import patch
from datetime import date
from models import City, Hotel, Booking
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
def test_flow_search_with_preferences_detailed(client, setup_search_data):
    search_params = {
        "startCity": "Warszawa",
        "visitedCity": "Nowy Jork",
        "startDate": "2027-06-01",
        "endDate": "2027-06-07",
        "guests": 2,
        "maxPrice": 20000.0,
        "minRating": 4.0
    }
    
    with patch("routers.stays.generate_stay_proposals") as mock_gen:
        mock_gen.return_value = 0 
        response = client.get("/results", params=search_params)

    assert response.status_code == 200
    assert "Plaza Hotel" in response.text
    
    assert "WiFi" in response.text
    assert "Basen" in response.text 
    assert "9150" in response.text  