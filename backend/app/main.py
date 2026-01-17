from fastapi import FastAPI, Depends, HTTPException, Query
from models.booking import Booking
from models.city import City
from sqlalchemy.orm import Session
from datetime import date
from database import engine, Base
from database import get_db
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from services.stay_service import generate_stay_proposals
from database import SessionLocal

app = FastAPI()
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

def get_booked_count():
    db = SessionLocal()
    try:
        return db.query(Booking).filter(Booking.status == "booked").count()
    finally:
        db.close()

templates.env.globals.update(booked_count=get_booked_count)

@app.get("/")
@app.get("/results")
async def show_results(
    request: Request,
    startDate: date = None, endDate: date = None,
    guests: int = None, startCity: str = None, visitedCity: str = None,
    minPrice: float = 0, maxPrice: float = 20000,
    minRating: float = 0,
    db: Session = Depends(get_db)
):
    if startDate and endDate and startCity and visitedCity:
        generate_stay_proposals(db, startDate, endDate, startCity, visitedCity)
        
        bookings = db.query(Booking).filter(
            Booking.status == "prepared",
            Booking.start_date == startDate,
            Booking.end_date == endDate,
            Booking.start_city_id == db.query(City).filter(City.name == startCity).first().id,
            Booking.visited_city_id == db.query(City).filter(City.name == visitedCity).first().id,
            Booking.total_price >= minPrice,
            Booking.total_price <= maxPrice,
            Booking.rating >= minRating,
            Booking.guests == guests
        ).all()
        
        if not bookings:
            return templates.TemplateResponse("results.html", {"request": request, "bookings": [], "empty": True})
        
        return templates.TemplateResponse("results.html", {"request": request, "bookings": bookings, "empty": False})
    
    specials = db.query(Booking).filter(Booking.status == "prepared").all()
    return templates.TemplateResponse("results.html", {"request": request, "bookings": specials, "empty": False})

@app.get("/details/{booking_id}")
async def get_details(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("details.html", {"request": request, "booking": booking})

@app.post("/book/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    booking.status = "booked"
    db.commit()
    return RedirectResponse(url="/my-bookings", status_code=303)

@app.get("/my-bookings")
async def my_bookings(request: Request, db: Session = Depends(get_db)):
    booked_stays = db.query(Booking).filter(Booking.status == "booked").all()
    return templates.TemplateResponse("booked.html", {"request": request, "bookings": booked_stays})