import sys
import os
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine, Base
from models.booking import Booking
from models.city import City
from models.hotel import Hotel
from models.flight import Flight
from models.transfer import Transfer

def seed_data():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    past_start = datetime.date(2025, 10, 10)
    past_end = past_start + datetime.timedelta(days=7)
    future_date = datetime.date(2026, 6, 15)

    try:
        # (bezpiecznik)
        if db.query(City).count() == 0:
            print("BŁĄD: Tabela miast jest pusta! Uruchom najpierw seeder_initial.py")
            return

        # 2. Hotele
        h1 = Hotel(name="Hotel Le Marais Boutique", address="Rue de Rivoli 12, Paryż", capacity=4, 
                   start_date=datetime.date(2024, 1, 1), end_date=datetime.date(2027, 12, 31),
                   rating=4.8, price=450.0, city_id=1, has_wifi=True, has_pool=False, has_restaurant=True)
        
        h2 = Hotel(name="Park Hyatt Tokyo", address="3-7-1-2 Nishi-Shinjuku, Tokio", capacity=2, 
                   start_date=datetime.date(2024, 1, 1), end_date=datetime.date(2027, 12, 31),
                   rating=4.9, price=1200.0, city_id=4, has_wifi=True, has_pool=True, has_restaurant=True)
        
        h4 = Hotel(name="Marriott Mena House", address="6 Pyramids Road, Kair", capacity=5, 
                   start_date=datetime.date(2024, 1, 1), end_date=datetime.date(2027, 12, 31),
                   rating=4.7, price=600.0, city_id=17, has_wifi=True, has_pool=True, has_restaurant=True)

        db.add_all([h1, h2, h4])
        db.flush() 

        # 3. Loty
        f1_tam = Flight(name="LOT LO341", start_city_id=2, end_city_id=1, date=past_start, price=400.0)
        f1_pow = Flight(name="LOT LO342", start_city_id=1, end_city_id=2, date=past_end, price=350.0)
        
        f2_tam = Flight(name="Air France AF274", start_city_id=1, end_city_id=4, date=future_date, price=2500.0)
        f2_pow = Flight(name="Air France AF275", start_city_id=4, end_city_id=1, date=future_date + datetime.timedelta(days=3), price=2400.0)
        
        f3_tam = Flight(name="ITA AZ792", start_city_id=2, end_city_id=4, date=future_date + datetime.timedelta(days=30), price=2800.0)
        f3_pow = Flight(name="ITA AZ793", start_city_id=4, end_city_id=2, date=future_date + datetime.timedelta(days=35), price=2700.0)
        
        f4_tam = Flight(name="EgyptAir MS791", start_city_id=2, end_city_id=17, date=future_date + datetime.timedelta(days=120), price=1200.0)
        f4_pow = Flight(name="EgyptAir MS792", start_city_id=17, end_city_id=2, date=future_date + datetime.timedelta(days=126), price=1100.0)
        
        db.add_all([f1_tam, f1_pow, f2_tam, f2_pow, f3_tam, f3_pow, f4_tam, f4_pow])
        db.flush()

        # 4. Transfery
        t_par = Transfer(type="Private Car", name="Mercedes S-Class", date=past_start, rating=5.0, price=200.0, city_id=1)
        t_tok = Transfer(type="Shuttle", name="Airport Limousine Bus", date=future_date, rating=4.5, price=100.0, city_id=4)
        t_kai = Transfer(type="Van", name="Tourism Van Cairo", date=future_date + datetime.timedelta(days=120), rating=4.2, price=150.0, city_id=17)
        
        db.add_all([t_par, t_tok, t_kai])
        db.flush()

        # 5. Rezerwacje
        test_cases = [
            Booking(status="completed", start_date=past_start, end_date=past_end,
                    guests=2, total_price=2400.0, visited_city_id=1, start_city_id=2,
                    hotel_id=h1.id, start_flight_id=f1_tam.id, end_flight_id=f1_pow.id, 
                    start_transfer_id=t_par.id, end_transfer_id=t_par.id),
                
            Booking(status="canceled", start_date=future_date, end_date=future_date + datetime.timedelta(days=3),
                    guests=1, total_price=1200.0, visited_city_id=4, start_city_id=1,
                    hotel_id=h2.id, start_flight_id=f2_tam.id, end_flight_id=f2_pow.id, 
                    start_transfer_id=t_tok.id, end_transfer_id=t_tok.id),

            Booking(status="special", start_date=future_date + datetime.timedelta(days=30), 
                    end_date=future_date + datetime.timedelta(days=35),
                    guests=2, total_price=1600.0, discount=20.0, visited_city_id=4, start_city_id=2,
                    hotel_id=h2.id, start_flight_id=f3_tam.id, end_flight_id=f3_pow.id, 
                    start_transfer_id=t_tok.id, end_transfer_id=t_tok.id),

            Booking(status="special", start_date=future_date + datetime.timedelta(days=120), 
                    end_date=future_date + datetime.timedelta(days=126),
                    guests=4, total_price=76000.0, discount=60.0, visited_city_id=17, start_city_id=2,
                    hotel_id=h4.id, start_flight_id=f4_tam.id, end_flight_id=f4_pow.id, 
                    start_transfer_id=t_kai.id, end_transfer_id=t_kai.id)
        ]

        db.add_all(test_cases)
        db.commit()
        print("Sukces: Zaaplikowano dane testowe!")

    except Exception as e:
        db.rollback()
        print(f"BŁĄD: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()