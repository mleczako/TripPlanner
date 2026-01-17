from sqlalchemy.orm import Session
from datetime import date
from models import Booking, City, Flight, Hotel, Transfer

def generate_stay_proposals(
    db: Session,
    start_date: date,
    end_date: date,
    start_city_name: str,
    visited_city_name: str
) -> int:
    s_city = db.query(City).filter(City.name == start_city_name).first()
    v_city = db.query(City).filter(City.name == visited_city_name).first()

    if not s_city or not v_city:
        return 0

    flights_to = db.query(Flight).filter(
        Flight.start_city_id == s_city.id,
        Flight.end_city_id == v_city.id,
        Flight.date == start_date
    ).all()

    flights_back = db.query(Flight).filter(
        Flight.start_city_id == v_city.id,
        Flight.end_city_id == s_city.id,
        Flight.date == end_date
    ).all()

    hotels = db.query(Hotel).filter(
        Hotel.city_id == v_city.id,
        Hotel.start_date <= start_date,
        Hotel.end_date >= end_date
    ).all()

    transfers = db.query(Transfer).filter(Transfer.city_id == v_city.id).all()

    if not flights_to or not flights_back or not hotels or not transfers:
        return 0

    new_bookings_count = 0
    nights = (end_date - start_date).days

    for f_to in flights_to:
        for f_back in flights_back:
            for hotel in hotels:
                for t1 in transfers:
                    for t2 in transfers:
                        existing = db.query(Booking).filter(
                            Booking.start_flight_id == f_to.id,
                            Booking.end_flight_id == f_back.id,
                            Booking.hotel_id == hotel.id,
                            Booking.start_transfer_id == t1.id,
                            Booking.end_transfer_id == t2.id
                        ).first()

                        if existing:
                            continue

                        total_price = f_to.price + f_back.price + (hotel.price * nights) + t1.price + t2.price
                        avg_rating = (hotel.rating + t1.rating + t2.rating) / 3

                        new_booking = Booking(
                            status="prepared",
                            hotel_id=hotel.id,
                            start_transfer_id=t1.id,
                            end_transfer_id=t2.id,
                            start_flight_id=f_to.id,
                            end_flight_id=f_back.id,
                            start_date=start_date,
                            end_date=end_date,
                            guests=hotel.capacity,
                            start_city_id=s_city.id,
                            visited_city_id=v_city.id,
                            total_price=total_price,
                            rating=round(avg_rating, 2)
                        )
                        db.add(new_booking)
                        new_bookings_count += 1

    db.commit()
    return new_bookings_count