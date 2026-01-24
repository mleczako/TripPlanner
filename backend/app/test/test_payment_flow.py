import pytest
from datetime import date
from unittest.mock import patch
from models import Booking, City, Hotel, Flight, Transfer, Event

def prepare_test_data(db):
    c1 = City(id=1, name="Warszawa")
    c2 = City(id=2, name="Berlin")
    db.add_all([c1, c2])
    db.flush()

    h = Hotel(id=1, name="Test Hotel", price=100, city_id=2, start_date=date.today(), end_date=date.today(), rating=5.0, capacity=2)
    f1 = Flight(id=1, name="FL1", start_city_id=1, end_city_id=2, date=date.today(), price=50)
    f2 = Flight(id=2, name="FL2", start_city_id=2, end_city_id=1, date=date.today(), price=50)
    t1 = Transfer(id=1, name="T1", type="Taxi", city_id=2, date=date.today(), price=20, rating=5.0)
    
    db.add_all([h, f1, f2, t1])
    db.flush()

    booking = Booking(
        id=99,
        status="prepared",
        visited_city_id=2,
        start_city_id=1,
        hotel_id=1,
        start_flight_id=1,
        end_flight_id=2,
        start_transfer_id=1,
        end_transfer_id=1,
        start_date=date(2025, 5, 1),
        end_date=date(2025, 5, 5),
        guests=2,
        total_price=1000.0
    )
    db.add(booking)
    db.commit()


def test_payment_page_load(client, db_session):
    prepare_test_data(db_session)
    
    response = client.get("/payment/99")
    
    assert response.status_code == 200
    assert "Opłacanie pobytu" in response.text
    
    b = db_session.query(Booking).filter(Booking.id == 99).first()
    assert b.status == "pending"

@patch("requests.post")
def test_process_payment_success(mock_post, client, db_session):
    prepare_test_data(db_session)
    
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"status": "success"}

    
    response = client.post("/payment/99", data={
        "paymentMethod": "blik",
        "paymentToken": "123456",
        "action": "pay"
    })

    assert response.status_code == 200 
    
    b = db_session.query(Booking).filter(Booking.id == 99).first()
    assert b.status == "booked"