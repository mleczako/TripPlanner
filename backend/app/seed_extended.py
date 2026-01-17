import datetime
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import random

def seed_extended_data():
    db = SessionLocal()
    try:
        cities = db.query(models.City).all()
        if not cities:
            print("Błąd: Najpierw zrób seed miast!")
            return

        # Sprawdź, czy hotele już istnieją
        if db.query(models.Hotel).count() > 0:
            print("Dane (hotele/loty) już są w bazie. Pomijam.")
            return

        print("Generowanie hoteli, transferów i lotów...")

        # Daty bazowe dla testów (Maj 2024)
        date_start = datetime.date(2024, 5, 1)
        date_end = datetime.date(2024, 5, 30)

        for city in cities:
            # --- 1. DODAWANIE HOTELI (3 na miasto) ---
            for i in range(1, 4):
                new_hotel = models.Hotel(
                    name=f"Hotel {city.name} {['Grand', 'Resort', 'Standard'][i-1]}",
                    address=f"ul. Turystyczna {random.randint(1, 100)}, {city.name}",
                    capacity=random.choice([2, 4, 6]),
                    start_date=date_start,
                    end_date=date_end,
                    rating=round(random.uniform(7.0, 9.9), 1),
                    price=random.randint(200, 800),
                    city_id=city.id
                )
                db.add(new_hotel)

            # --- 2. DODAWANIE TRANSFERÓW (2 na miasto) ---
            types = [("Taxi", 50, 9.0), ("Bus", 15, 7.5)]
            for t_type, t_price, t_rating in types:
                new_transfer = models.Transfer(
                    type=t_type,
                    name=f"{t_type} {city.name} Express",
                    date=date_start, # Dostępne ogólnie w maju
                    rating=t_rating,
                    price=t_price,
                    city_id=city.id
                )
                db.add(new_transfer)

            types = [("Taxi", 50, 9.0), ("Bus", 15, 7.5)]
            for t_type, t_price, t_rating in types:
                new_transfer = models.Transfer(
                    type=t_type,
                    name=f"{t_type} {city.name} Express",
                    date=date_end, # Dostępne ogólnie w maju
                    rating=t_rating,
                    price=t_price,
                    city_id=city.id
                )
                db.add(new_transfer)

        # --- 3. DODAWANIE LOTÓW ---
        # Stworzymy loty z Paryża (ID 1) do wszystkich innych miast i z powrotem
        paryz = db.query(models.City).filter(models.City.name == "Paryż").first()
        
        if paryz:
            for city in cities:
                if city.id == paryz.id: continue

                # Lot TAM (np. 1 maja i 10 maja)
                for day in [1, 10]:
                    flight_date = datetime.date(2024, 5, day)
                    # Lot DO
                    db.add(models.Flight(
                        name=f"Air {city.name} Express",
                        start_city_id=paryz.id,
                        end_city_id=city.id,
                        date=flight_date,
                        price=random.randint(300, 1200)
                    ))
                    # Lot POWROTNY (np. 5 maja i 15 maja)
                    db.add(models.Flight(
                        name=f"Air Paryż Return",
                        start_city_id=city.id,
                        end_city_id=paryz.id,
                        date=flight_date + datetime.timedelta(days=29),
                        price=random.randint(300, 1200)
                    ))

        db.commit()
        print("Gotowe! Baza zawiera teraz miasta, hotele, transfery i loty.")

    except Exception as e:
        print(f"Błąd: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_extended_data()