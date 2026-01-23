import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

from database import Base, get_db
from main import app
from models.booking import Booking
from models.city import City
from models.hotel import Hotel
from models.flight import Flight
from models.transfer import Transfer

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def prepare_cities_data(db):
    c1 = City(id=1, name="Paryż")
    c2 = City(id=2, name="Tokio")
    c3 = City(id=3, name="Kair")
    db.add_all([c1, c2, c3])
    db.flush()

def prepare_booking_data(db, id, status, city_name, visited_city_id, start_city_id, start_date, end_date, total_price, discount):
    hotel = Hotel(
        id=id, name=f"{city_name} Luxury Hotel", price=500.0, city_id=visited_city_id, 
        rating=4.5, address=f"{city_name} St 1", capacity=10
    )
    f_start = Flight(id=id*10+1, name="LO123", price=400.0, start_city_id=start_city_id, end_city_id=visited_city_id, date=start_date)
    f_end = Flight(id=id*10+2, name="LO124", price=350.0, start_city_id=visited_city_id, end_city_id=start_city_id, date=end_date)
    t_start = Transfer(id=id*10+1, name="Airport Shuttle", price=50.0, type="Van", rating=4.8, city_id=visited_city_id)
    t_end = Transfer(id=id*10+2, name="Private Car", price=80.0, type="Sedan", rating=5.0, city_id=visited_city_id)

    db.add_all([hotel, f_start, f_end, t_start, t_end])
    db.flush()
    
    db.add(Booking(
        id=id, 
        status=status, 
        visited_city_id=visited_city_id, 
        start_city_id=start_city_id,
        hotel_id=hotel.id,
        start_flight_id=f_start.id,
        end_flight_id=f_end.id,
        start_transfer_id=t_start.id,
        end_transfer_id=t_end.id,
        total_price=total_price, 
        discount=discount, 
        start_date=start_date, 
        end_date=end_date, 
        guests=4
    ))
    db.commit()
    db.close()

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    prepare_cities_data(db)
    prepare_booking_data(
        db, id=1, status="completed", city_name="Paryż", visited_city_id=1, start_city_id=2,
        start_date=date(2025, 10, 10), end_date=date(2025, 10, 17),
        total_price=2400, discount=None
    )
    prepare_booking_data(
        db, id=2, status="canceled", city_name="Tokio", visited_city_id=2, start_city_id=1,
        start_date=date(2026, 6, 15), end_date=date(2026, 6, 20),
        total_price=1200, discount=None
    )
    prepare_booking_data(
        db, id=3, status="special", city_name="Tokio", visited_city_id=2, start_city_id=1,
        start_date=date(2026, 7, 15), end_date=date(2026, 7, 20),
        total_price=1600, discount=20
    )
    prepare_booking_data(
        db, id=4, status="special", city_name="Kair", visited_city_id=3, start_city_id=2,
        start_date=date(2026, 10, 13), end_date=date(2026, 11, 7),
        total_price=76000, discount=60
    )
    
    yield
    Base.metadata.drop_all(bind=engine)

def test_special_offers_pobyt_id():
    """KROK 1: Weryfikacja czy /special-offers zwraca Tokio (ID 3) i Kair (ID 4)"""
    response = client.get("/special-offers")
    assert response.status_code == 200
    
    assert "Tokio" in response.text
    assert "Kair" in response.text
    assert "Paryż" not in response.text

def test_special_offers_pricing_logic():
    """KROK 2: Weryfikacja wyliczeń cenowych i badge'y zniżek"""
    response = client.get("/special-offers")
    assert response.status_code == 200

    assert "1600" in response.text
    assert "2000" in response.text
    assert "-20%" in response.text

    assert "76000" in response.text
    assert "190000" in response.text
    assert "-60%" in response.text

def test_special_offer_details_labels():
    """KROK 3: Weryfikacja detali oferty w /details/4"""
    response = client.get("/details/4")
    assert response.status_code == 200

    assert "LAST MINUTE" in response.text
    assert "-60%" in response.text
    assert "76000" in response.text
    assert "190000" in response.text