from fastapi.templating import Jinja2Templates
from database import SessionLocal
from models.booking import Booking
from datetime import date

templates = Jinja2Templates(directory="templates")

def get_booked_count():
    db = SessionLocal()
    try:
        return db.query(Booking).filter(Booking.status == "booked").count()
    finally:
        db.close()

templates.env.globals.update(booked_count=get_booked_count)
templates.env.globals.update(today=date.today().isoformat())