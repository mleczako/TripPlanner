import pytest
from datetime import date
from models import Booking, City, Hotel, Flight, Transfer

def prepare_booking(db):
    c1 = City(id=1, name="Warszawa")
    c2 = City(id=2, name="Kraków")
    db.add_all([c1, c2])
    db.flush()

    h = Hotel(id=1, name="Error Hotel", price=100, city_id=2, start_date=date.today(), end_date=date.today(), rating=5.0, capacity=2)
    f1 = Flight(id=1, name="F1", start_city_id=1, end_city_id=2, date=date.today(), price=50)
    f2 = Flight(id=2, name="F2", start_city_id=2, end_city_id=1, date=date.today(), price=50)
    t1 = Transfer(id=1, name="T1", type="Taxi", city_id=2, date=date.today(), price=20, rating=5.0)
    
    db.add_all([h, f1, f2, t1])
    db.flush()

    booking = Booking(
        id=100, 
        status="prepared",
        visited_city_id=2,
        start_city_id=1,
        hotel_id=1,
        start_flight_id=1,
        end_flight_id=2,
        start_transfer_id=1,
        end_transfer_id=1,
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 7),
        guests=2,
        total_price=500.0
    )
    db.add(booking)
    db.commit()


def test_payment_invalid_blik_code(client, db_session):

    prepare_booking(db_session)

    response = client.post("/payment/100", data={
        "paymentMethod": "blik",
        "paymentToken": "ABC", 
        "action": "pay"
    })

    assert response.status_code == 200
    
    assert "Nieprawidłowy kod BLIK" in response.text

    b = db_session.query(Booking).filter(Booking.id == 100).first()
    assert b.status != "booked"

def test_payment_non_existent_booking(client, db_session):

    response = client.get("/payment/9999")
    
    assert response.status_code == 404
    assert "detail" in response.json() 