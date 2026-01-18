from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import requests
from models import Booking, City, Flight, Hotel, Transfer

MOCK_API_URL = "http://localhost:8001"

def generate_stay_proposals(
    db: Session,
    start_date: date,
    end_date: date,
    start_city_name: str,
    visited_city_name: str,
    guests: int
) -> int:
    s_city = db.query(City).filter(func.lower(City.name) == start_city_name.lower()).first()
    v_city = db.query(City).filter(func.lower(City.name) == visited_city_name.lower()).first()

    if not s_city or not v_city:
        print(f"[StayService] [ERROR] Nie znaleziono miast w bazie lokalnej: {start_city_name} lub {visited_city_name}")
        return 0

    print(f"\n[StayService] [START] Rozpoczynam wyszukiwanie ofert: {s_city.name} -> {v_city.name}")

    try:
        print(f"[StayService] [HTTP GET] Odpytuje External Hotel API o noclegi w: {v_city.name}...")
        resp_h = requests.get(f"{MOCK_API_URL}/external/hotels", 
                              params={"city": v_city.name, "date_from": start_date, "date_to": end_date, "guests": guests})
        hotels_data = resp_h.json() if resp_h.status_code == 200 else []
        print(f"[StayService]    [OK] Otrzymano {len(hotels_data)} hoteli.")

        print(f"[StayService] [HTTP GET] Odpytuje External Flight API o loty: {s_city.name} -> {v_city.name}...")
        resp_f1 = requests.get(f"{MOCK_API_URL}/external/flights",
                               params={"origin": s_city.name, "destination": v_city.name, "date": start_date})
        flights_to_data = resp_f1.json() if resp_f1.status_code == 200 else []
        print(f"[StayService]    [OK] Otrzymano {len(flights_to_data)} opcji lotu tam.")

        print(f"[StayService] [HTTP GET] Odpytuje External Flight API o loty: {v_city.name} -> {s_city.name}...")
        resp_f2 = requests.get(f"{MOCK_API_URL}/external/flights",
                               params={"origin": v_city.name, "destination": s_city.name, "date": end_date})
        flights_back_data = resp_f2.json() if resp_f2.status_code == 200 else []
        print(f"[StayService]    [OK] Otrzymano {len(flights_back_data)} opcji lotu powrotnego.")

        print(f"[StayService] [HTTP GET] Odpytuje External Transfer API o transport w: {v_city.name}...")
        resp_t = requests.get(f"{MOCK_API_URL}/external/transfers", params={"city": v_city.name})
        transfers_data = resp_t.json() if resp_t.status_code == 200 else []
        print(f"[StayService]    [OK] Otrzymano {len(transfers_data)} opcji transferu.")
        
    except Exception as e:
        print(f"[StayService] [CRITICAL] Blad polaczenia z API Zewnetrznym: {e}")
        raise ConnectionError("Błąd połączenia z Mock API") 
        

    if not flights_to_data or not flights_back_data or not hotels_data or not transfers_data:
        print("[StayService] [WARN] Brak kompletnych danych z API (brakuje lotow lub hoteli). Przerywam.")
        return 0

    new_bookings_count = 0
    nights = (end_date - start_date).days

    print(f"[StayService] [INFO] Przetwarzanie i laczenie danych w pakiety (Algorytm Sklejania)...")

    for f_to_json in flights_to_data:
        f_to_obj = _get_or_create_flight(db, f_to_json, s_city.id, v_city.id, start_date)
        
        for f_back_json in flights_back_data:
            f_back_obj = _get_or_create_flight(db, f_back_json, v_city.id, s_city.id, end_date)

            for hotel_json in hotels_data:
                hotel_obj = _get_or_create_hotel(db, hotel_json, v_city.id, start_date, end_date)

                for t1_json in transfers_data:
                    t1_obj = _get_or_create_transfer(db, t1_json, v_city.id, start_date)

                    for t2_json in transfers_data:
                        t2_obj = _get_or_create_transfer(db, t2_json, v_city.id, end_date)

                        existing = db.query(Booking).filter(
                            Booking.start_flight_id == f_to_obj.id,
                            Booking.end_flight_id == f_back_obj.id,
                            Booking.hotel_id == hotel_obj.id,
                            Booking.start_transfer_id == t1_obj.id,
                            Booking.end_transfer_id == t2_obj.id
                        ).first()

                        if existing:
                            continue

                        total_price = f_to_json['price'] + f_back_json['price'] + \
                                      (hotel_json['price_per_night'] * nights) + \
                                      t1_json['price'] + t2_json['price']
                        
                        avg_rating = (hotel_json['rating'] + t1_json['rating'] + t2_json['rating']) / 3

                        new_booking = Booking(
                            status="prepared",
                            hotel_id=hotel_obj.id,
                            start_transfer_id=t1_obj.id,
                            end_transfer_id=t2_obj.id,
                            start_flight_id=f_to_obj.id,
                            end_flight_id=f_back_obj.id,
                            start_date=start_date,
                            end_date=end_date,
                            guests=hotel_json['capacity'],
                            start_city_id=s_city.id,
                            visited_city_id=v_city.id,
                            total_price=total_price,
                            rating=round(avg_rating, 2)
                        )
                        db.add(new_booking)
                        new_bookings_count += 1

    db.commit()
    print(f"[StayService] [END] Zakonczono. Wygenerowano i zapisano w bazie {new_bookings_count} unikalnych ofert pobytu.\n")
    return new_bookings_count

def _get_or_create_hotel(db: Session, data: dict, city_id: int, s_date, e_date):
    hotel = db.query(Hotel).filter(Hotel.name == data['name']).first()
    if not hotel:
        hotel = Hotel(
            name=data['name'],
            address=data['address'],
            capacity=data['capacity'],
            start_date=s_date,
            end_date=e_date,
            rating=data['rating'],
            price=data['price_per_night'],
            city_id=city_id
        )
        db.add(hotel)
    else:
        hotel.price = data['price_per_night']
        hotel.rating = data['rating']
        hotel.capacity = data['capacity'] 
    
    db.flush()
    db.refresh(hotel)
    return hotel

def _get_or_create_flight(db: Session, data: dict, start_city_id: int, end_city_id: int, f_date):
    flight = db.query(Flight).filter(Flight.name == data['flight_number']).first()
    if not flight:
        flight = Flight(
            name=data['flight_number'],
            start_city_id=start_city_id,
            end_city_id=end_city_id,
            date=f_date,
            price=data['price']
        )
        db.add(flight)
    else:
        flight.price = data['price']

    db.flush()
    db.refresh(flight)
    return flight

def _get_or_create_transfer(db: Session, data: dict, city_id: int, t_date):
    if 'name' not in data:
        data['name'] = f"Unknown Transfer {data.get('type', 'Transport')}"

    transfer = db.query(Transfer).filter(Transfer.name == data['name']).first()
    if not transfer:
        transfer = Transfer(
            type=data['type'],
            name=data['name'],
            date=t_date,
            rating=data['rating'],
            price=data['price'],
            city_id=city_id
        )
        db.add(transfer)
    else:
        transfer.price = data['price']
        transfer.rating = data['rating']

    db.flush()
    db.refresh(transfer)
    return transfer