from datetime import date, datetime, timedelta
import random

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.entities import (
    Flight,
    Hotel,
    HotelAvailability,
    Transfer,
    NewsEvent,
)


BASE_DATE = date(2026, 1, 1)
CITIES = ["MAD", "BCN", "ROM", "PAR", "BER"]



def seed():
    db: Session = SessionLocal()

    try:
        print("Seeding database...")

        flights = []

    
        for day in range(10):
            out_date = BASE_DATE + timedelta(days=day)
            back_date = out_date + timedelta(days=5)

            for city in CITIES:
              
                flights.append(
                    Flight(
                        from_airport="WAW",
                        to_airport=city,
                        date=out_date,
                        price=300,
                        status="SCHEDULED",
                    )
                )
               
                flights.append(
                    Flight(
                        from_airport="WAW",
                        to_airport=city,
                        date=out_date,
                        price=850,
                        status="SCHEDULED",
                    )
                )
              
                flights.append(
                    Flight(
                        from_airport=city,
                        to_airport="WAW",
                        date=back_date,
                        price=320,
                        status="SCHEDULED",
                    )
                )
             
                flights.append(
                    Flight(
                        from_airport=city,
                        to_airport="WAW",
                        date=back_date,
                        price=900,
                        status="SCHEDULED",
                    )
                )

        db.add_all(flights)
        print(f"Flights: {len(flights)}")

        hotels = []

        HOTEL_NAMES = {
            "MAD": [
                "Hotel Sol Madrid",
                "Gran Via Palace",
                "Royal Madrid Center",
                "Plaza Mayor Hotel",
                "Castilla Comfort Hotel",
            ],
            "BCN": [
                "Barcelona Beach Resort",
                "Hotel Catalunya Central",
                "Mediterranean Palace",
                "Costa Brava Inn",
                "Sagrada Familia Hotel",
            ],
            "ROM": [
                "Roma Imperial Hotel",
                "Colosseum View Inn",
                "Vatican Gardens Hotel",
                "Trastevere Boutique Hotel",
                "Roman Forum Palace",
            ],
            "PAR": [
                "Paris Lumière Hotel",
                "Champs-Élysées Palace",
                "Montmartre Boutique",
                "Eiffel Tower View Hotel",
                "Seine Riverside Inn",
            ],
            "BER": [
                "Berlin Central Hotel",
                "Brandenburg Gate Inn",
                "Museum Island Hotel",
                "Alexanderplatz Suites",
                "Checkpoint Charlie Hotel",
            ],
        }

        for city, names in HOTEL_NAMES.items():
            for name in names:
                hotels.append(
                    Hotel(
                        name=name,
                        location=city,
                        standard=random.randint(2, 5),
                        price_per_night=random.choice([180, 220, 260, 320, 400]),
                        has_wifi=True,
                        has_pool=random.choice([True, False]),
                        has_parking=random.choice([True, False]),
                    )
                )

        db.add_all(hotels)
        db.flush()  
        print(f"✔ Hotels: {len(hotels)}")

        availabilities = []

        for hotel in hotels:
            start = BASE_DATE

            for _ in range(random.randint(5, 8)):
                length = random.randint(4, 12)

                date_from = start
                date_to = start + timedelta(days=length)

                availabilities.append(
                    HotelAvailability(
                        hotel_id=hotel.id,
                        date_from=date_from,
                        date_to=date_to,
                        max_guests=random.choice([2, 3, 4, 5, 6]),
                        is_available=random.choice([True, True, True, False]),
                    )
                )

                start = date_to + timedelta(days=random.randint(1, 5))

        db.add_all(availabilities)
        print(f"✔ HotelAvailability: {len(availabilities)}")

        transfers = []

        for city in CITIES:
            transfers.extend(
                [
                    Transfer(type="BUS", location=city, price=40, available=True),
                    Transfer(type="TRAIN", location=city, price=60, available=True),
                    Transfer(type="TAXI", location=city, price=90, available=True),
                ]
            )

        db.add_all(transfers)
        print(f"✔ Transfers: {len(transfers)}")

        news = [
            NewsEvent(
                type="WEATHER_ALERT",
                location="PAR",
                start_time=datetime(2026, 1, 6, 6, 0),
                end_time=datetime(2026, 1, 7, 23, 0),
                severity="MEDIUM",
                processed=False,
            ),
            NewsEvent(
                type="AIRPORT_CLOSED",
                location="MAD",
                start_time=datetime(2026, 1, 10, 0, 0),
                end_time=datetime(2026, 1, 11, 23, 59),
                severity="HIGH",
                processed=False,
            ),
        ]

        db.add_all(news)
        print(f"✔ NewsEvents: {len(news)}")

        db.commit()
        print(" SEED COMPLETED SUCCESSFULLY")

    except Exception as e:
        db.rollback()
        print("SEED FAILED:", e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
