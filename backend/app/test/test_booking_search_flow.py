import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from models import Booking, City, Hotel, Flight, Transfer, Event

@pytest.fixture
def setup_search_data(db_session):
    waw = City(id=1, name="Warszawa", description="Stolica", image_url="img1.jpg")
    nyc = City(id=2, name="Nowy Jork", description="Big Apple", image_url="img2.jpg")
    db_session.add_all([waw, nyc])
    db_session.flush()

    h = Hotel(id=10, name="Plaza Hotel", address="5th Ave", capacity=2, 
              start_date=date(2027,6,1), end_date=date(2027,6,7), 
              rating=5.0, price=5000.0, city_id=2, 
              has_wifi=True, has_pool=True, has_restaurant=True)
    
    f1 = Flight(id=10, name="LOT 001", start_city_id=1, end_city_id=2, date=date(2027,6,1), price=2000.0)
    f2 = Flight(id=11, name="LOT 002", start_city_id=2, end_city_id=1, date=date(2027,6,7), price=2000.0)
    
    t1 = Transfer(id=10, name="Taxi VIP", type="Taxi", date=date(2027,6,1), rating=5.0, price=100.0, city_id=2)
    t2 = Transfer(id=11, name="Uber", type="Car", date=date(2027,6,7), rating=4.5, price=50.0, city_id=2)

    db_session.add_all([h, f1, f2, t1, t2])
    db_session.flush()

    booking = Booking(
        id=500,
        status="prepared",
        start_city_id=1,
        visited_city_id=2,
        hotel_id=10,
        start_flight_id=10, end_flight_id=11,
        start_transfer_id=10, end_transfer_id=11,
        start_date=date(2027, 6, 1),
        end_date=date(2027, 6, 7),
        guests=2,
        total_price=9150.0,
        rating=5.0
    )
    db_session.add(booking)
    db_session.commit()


@patch("services.stay_service.requests.get")
def test_search_results_filtering(mock_get, client, setup_search_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [] 
    mock_get.return_value = mock_response

    response = client.get("/results", params={
        "startCity": "Warszawa",
        "visitedCity": "Nowy Jork",
        "startDate": "2027-06-01",
        "endDate": "2027-06-07",
        "guests": 2,
        "maxPrice": 20000,
        "minRating": 4.0
    })

    assert response.status_code == 200
    content = response.text
    
    assert "Dostępne pobyty" in content
    assert "Nowy Jork" in content
    assert "Plaza Hotel" in content
    assert "9150" in content

@patch("services.stay_service.requests.get")
def test_search_results_filtering_empty(mock_get, client, setup_search_data):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_get.return_value = mock_response

    response = client.get("/results", params={
        "startCity": "Warszawa",
        "visitedCity": "Nowy Jork",
        "startDate": "2027-06-01",
        "endDate": "2027-06-07",
        "guests": 2,
        "maxPrice": 1000, 
        "minRating": 4.0
    })

    assert response.status_code == 200
    assert "Brak ofert spełniających" in response.text

def test_booking_details_page(client, setup_search_data):
    response = client.get("/details/500")
    assert response.status_code == 200
    assert "Nowy Jork - Pobyt" in response.text
    assert "Przejdź do płatności" in response.text