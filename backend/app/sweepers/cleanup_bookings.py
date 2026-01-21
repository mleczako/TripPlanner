import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.booking import Booking

def cleanup_bookings():
    db = SessionLocal()
    try:
        num_rows_deleted = db.query(Booking).delete()
        db.commit()
        print(f"Pomyślnie usunięto {num_rows_deleted} rezerwacji z bazy danych.")
    except Exception as e:
        print(f"Wystąpił błąd podczas usuwania danych: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_bookings()