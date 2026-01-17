from datetime import datetime, date, timedelta
from app.database import SessionLocal
from app.models.entities import (
    Flight,
    Hotel,
    HotelAvailability,
    Transfer,
    NewsEvent,
)
CITIES = ["MAD", "BCN", "LIS", "ROM", "PAR"]


def seed():
    db = SessionLocal()

    try:
        hotels = []
        for i in range(1, 51):
            city = CITIES[i % len(CITIES)]
            hotels.append(
                Hotel(
                    name=f"Hotel {city} #{i}",
                    location=city,
                    standard=(i % 5) + 1,
                    price_per_night=120 + (i % 8) * 30,
                    has_wifi=True,
                    has_pool=(i % 3 == 0),
                    has_parking=(i % 2 == 0),
                )
            )

        db.add_all(hotels)
        db.flush()  


        availability = []
        base_date = date(2026, 1, 1)

        for hotel in hotels:
            for j in range(12):
                start = base_date + timedelta(days=j * 14)
                end = start + timedelta(days=10)

                availability.append(
                    HotelAvailability(
                        hotel_id=hotel.id,
                        date_from=start,
                        date_to=end,
                        max_guests=(j % 4) + 1,
                        is_available=True if j % 6 != 0 else False,
                    )
                )

        db.add_all(availability)

        flights = []
        for i in range(50):
            city = CITIES[i % len(CITIES)]
            flight_date = base_date + timedelta(days=(i % 10) * 14 + 3)

            flights.append(
                Flight(
                    from_airport="WAW",
                    to_airport=city,
                    date=flight_date,
                    price=350 + (i % 10) * 40,
                    status="SCHEDULED",
                )
            )

        db.add_all(flights)

        transfers = []
        for city in CITIES:
            transfers.extend([
                Transfer(type="BUS", location=city, price=35, available=True),
                Transfer(type="TRAIN", location=city, price=55, available=True),
                Transfer(type="TAXI", location=city, price=120, available=True),
            ])

        db.add_all(transfers)

        news = []
        for i in range(10):
            city = CITIES[i % len(CITIES)]
            start = datetime.utcnow() + timedelta(days=i * 2)

            news.append(
                NewsEvent(
                    type="WEATHER_ALERT" if i % 2 == 0 else "TRANSPORT_STRIKE",
                    location=city,
                    start_time=start,
                    end_time=start + timedelta(hours=12),
                    severity="HIGH" if i % 3 == 0 else "MEDIUM",
                    processed=False,
                )
            )

        db.add_all(news)

        db.commit()
        print(" SEED COMPLETED – DATA IS CONSISTENT AND USABLE")

    except Exception as e:
        db.rollback()
        print("SEED FAILED:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()
