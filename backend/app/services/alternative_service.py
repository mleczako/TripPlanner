import math
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Booking, City, Hotel, Flight, Transfer

MOCK_API_URL = "http://localhost:8001"

def min_rating_floor(b: Booking) -> float:
    return float(math.floor(b.rating or 0))

def create_alternatives_for_disrupted_booking(db: Session, booking: Booking, max_alt: int = 5) -> int:
    if booking.status != "disrupted":
        return 0

    dtype = (booking.disruption_type or "").upper()

    if dtype in ["WEATHER", "SECURITY", "HOTEL"]:
        return _generate_full_alternative_stays(db, booking, max_alt)

    return 0

def _generate_full_alternative_stays(db: Session, original: Booking, max_alt: int) -> int:
    min_r = min_rating_floor(original)
    max_budget = original.total_price or 0
    nights = (original.end_date - original.start_date).days
    candidate_cities = db.query(City).filter(City.id != original.visited_city_id).limit(3).all()
    
    new_bookings_count = 0

    for city in candidate_cities:
        if new_bookings_count >= max_alt:
            break

        try:
            resp_h = requests.get(f"{MOCK_API_URL}/external/hotels", 
                                  params={"city": city.name, "date_from": original.start_date, "date_to": original.end_date, "guests": original.guests}, timeout=2)
            hotels_data = resp_h.json() if resp_h.status_code == 200 else []

            resp_f1 = requests.get(f"{MOCK_API_URL}/external/flights",
                                   params={"origin": original.start_city.name, "destination": city.name, "date": original.start_date}, timeout=2)
            flights_to_data = resp_f1.json() if resp_f1.status_code == 200 else []

            resp_f2 = requests.get(f"{MOCK_API_URL}/external/flights",
                                   params={"origin": city.name, "destination": original.start_city.name, "date": original.end_date}, timeout=2)
            flights_back_data = resp_f2.json() if resp_f2.status_code == 200 else []

            resp_t = requests.get(f"{MOCK_API_URL}/external/transfers", params={"city": city.name}, timeout=2)
            transfers_data = resp_t.json() if resp_t.status_code == 200 else []

        except Exception:
            continue

        for h_json in hotels_data:
            if h_json['rating'] < min_r: continue 
            
            for f_to_json in flights_to_data:
                for f_back_json in flights_back_data:
                    for t1_json in transfers_data:
                        for t2_json in transfers_data:
                            if new_bookings_count >= max_alt: break

                            total_price = f_to_json['price'] + f_back_json['price'] + \
                                          (h_json['price_per_night'] * nights) + \
                                          t1_json['price'] + t2_json['price']

                            if total_price > max_budget:
                                continue

                            h_obj = _get_or_create_hotel(db, h_json, city.id, original.start_date, original.end_date)
                            f_to_obj = _get_or_create_flight(db, f_to_json, original.start_city_id, city.id, original.start_date)
                            f_back_obj = _get_or_create_flight(db, f_back_json, city.id, original.start_city_id, original.end_date)
                            t1_obj = _get_or_create_transfer(db, t1_json, city.id, original.start_date)
                            t2_obj = _get_or_create_transfer(db, t2_json, city.id, original.end_date)

                            avg_rating = (h_json['rating'] + t1_json['rating'] + t2_json['rating']) / 3

                            alt_booking = Booking(
                                status="prepared",
                                parent_booking_id=original.id,
                                hotel_id=h_obj.id,
                                start_transfer_id=t1_obj.id,
                                end_transfer_id=t2_obj.id,
                                start_flight_id=f_to_obj.id,
                                end_flight_id=f_back_obj.id,
                                start_date=original.start_date,
                                end_date=original.end_date,
                                guests=original.guests,
                                start_city_id=original.start_city_id,
                                visited_city_id=city.id, 
                                total_price=total_price,
                                rating=round(avg_rating, 2)
                            )
                            db.add(alt_booking)
                            new_bookings_count += 1

    db.commit()
    return new_bookings_count

def _get_or_create_hotel(db, data, city_id, s_date, e_date):
    hotel = db.query(Hotel).filter(Hotel.name == data['name']).first()
    if not hotel:
        hotel = Hotel(
            name=data['name'], address=data['address'], capacity=data['capacity'],
            start_date=s_date, end_date=e_date, rating=data['rating'],
            price=data['price_per_night'], city_id=city_id,
            has_wifi=data.get("has_wifi", False), has_pool=data.get("has_pool", False),
            has_restaurant=data.get("has_restaurant", False)
        )
        db.add(hotel)
    db.flush()
    return hotel

def _get_or_create_flight(db, data, start_city_id, end_city_id, f_date):
    flight = db.query(Flight).filter(Flight.name == data['flight_number']).first()
    if not flight:
        flight = Flight(name=data['flight_number'], start_city_id=start_city_id, 
                        end_city_id=end_city_id, date=f_date, price=data['price'])
        db.add(flight)
    db.flush()
    return flight

def _get_or_create_transfer(db, data, city_id, t_date):
    name = data.get('name', f"Transfer {data.get('type')}")
    transfer = db.query(Transfer).filter(Transfer.name == name).first()
    if not transfer:
        transfer = Transfer(type=data['type'], name=name, date=t_date, 
                            rating=data['rating'], price=data['price'], city_id=city_id)
        db.add(transfer)
    db.flush()
    return transfer