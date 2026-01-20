from fastapi import FastAPI, Depends, HTTPException, Query, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import requests
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from database import engine, Base, get_db, SessionLocal
from models.booking import Booking
from models.city import City
from services.stay_service import generate_stay_proposals

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
    minPrice: float = 0, maxPrice: float = 100000,
    minRating: float = 0,
    db: Session = Depends(get_db)
):
    context = {"request": request, "bookings": [], "empty": False, "api_error": False}

    if startDate and endDate and startCity and visitedCity:
        try:
            generate_stay_proposals(db, startDate, endDate, startCity, visitedCity, guests)
        except ConnectionError:
            print("LOG: Wykryto awarię API!")
            context["api_error"] = True
            return templates.TemplateResponse("results.html", context)
        except Exception as e:
            print(f"LOG: Inny błąd API: {e}")

        start_city_obj = db.query(City).filter(func.lower(City.name) == startCity.lower()).first()
        visited_city_obj = db.query(City).filter(func.lower(City.name) == visitedCity.lower()).first()
        
        if not start_city_obj or not visited_city_obj:
             context["empty"] = True
             return templates.TemplateResponse("results.html", context)

        raw_bookings = db.query(Booking).filter(
            Booking.status == "prepared",
            Booking.start_date == startDate,
            Booking.end_date == endDate,
            Booking.start_city_id == start_city_obj.id,
            Booking.visited_city_id == visited_city_obj.id
        ).all()
        
        print(f"[DEBUG] W bazie istnieje {len(raw_bookings)} ofert na tej trasie (przed filtracją ceny/osób).")

        valid_bookings = []
        for b in raw_bookings:
            if b.guests >= guests and minPrice <= b.total_price <= maxPrice and b.rating >= minRating:
                valid_bookings.append(b)
        
        print(f"[DEBUG] Po filtracji zostało {len(valid_bookings)} ofert.")
        
        if not valid_bookings:
            print(f"[DEBUG] Wszystkie oferty odrzucone! Sprawdź maxPrice. Przykładowa cena w bazie: {raw_bookings[0].total_price if raw_bookings else 'Brak'}")
            context["empty"] = True
        else:
            context["bookings"] = valid_bookings
        
        return templates.TemplateResponse("results.html", context)
    
    specials = db.query(Booking).filter(Booking.status == "prepared").limit(3).all()
    context["bookings"] = specials
    return templates.TemplateResponse("results.html", context)

@app.get("/details/{booking_id}")
async def get_details(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("details.html", {"request": request, "booking": booking})

@app.post("/book/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        booking.status = "booked"
        db.commit()
    return RedirectResponse(url="/my-bookings", status_code=303)





@app.get("/payment/{booking_id}")
async def payment_page(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)
    
    if booking.status == "prepared":
        booking.status = "pending"
        db.commit()
    # ---------------------------------------------------------------
    
    return templates.TemplateResponse("payment.html", {
        "request": request, 
        "booking": booking
    })

@app.post("/payment/{booking_id}")
async def process_payment(
    booking_id: int, 
    request: Request,
    paymentMethod: str = Form(None), 
    paymentToken: str = Form(None),
    action: str = Form(...), 
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)

    if action == "cancel":
        print(f"LOG: Użytkownik anulował płatność dla rezerwacji {booking_id}")
        
        booking.status = "prepared"
        db.commit()
        # ------------------------------------------------------------
        
        return RedirectResponse(url=f"/details/{booking_id}", status_code=303)

    if not paymentMethod or not paymentToken:
        return templates.TemplateResponse("payment.html", {
            "request": request, 
            "booking": booking, 
            "error": "Musisz wybrać metodę płatności i wpisać kod/numer karty."
        })

    MOCK_API_URL = "http://localhost:8001"
    
    try:
        response = requests.post(f"{MOCK_API_URL}/external/payment", json={
            "amount": booking.total_price,
            "currency": "PLN",
            "method": paymentMethod,
            "token": paymentToken
        })
        
        if response.status_code == 200:
            try:
                confirm_payload = {
                    "booking_reference": str(booking.id),
                    "items": [f"hotel_{booking.hotel_id}", f"flight_{booking.start_flight_id}"]
                }
                requests.post(f"{MOCK_API_URL}/external/finalize", json=confirm_payload)
            except:
                pass

            booking.status = "booked"
            db.commit()
            return RedirectResponse(url="/my-bookings", status_code=303)
        else:
           
            error_detail = response.json().get('detail', 'Transakcja odrzucona')
            return templates.TemplateResponse("payment.html", {
                "request": request, 
                "booking": booking, 
                "error": f"Błąd autoryzacji: {error_detail}. Spróbuj ponownie."
            })

    except requests.exceptions.ConnectionError:
        return templates.TemplateResponse("payment.html", {
            "request": request, 
            "booking": booking, 
            "error": "Błąd systemowy: Nie można połączyć się z operatorem płatności."
        })
    
@app.get("/my-bookings")
async def my_bookings(request: Request, db: Session = Depends(get_db)):
    booked_stays = db.query(Booking).filter(Booking.status == "booked").all()
    return templates.TemplateResponse("booked.html", {"request": request, "bookings": booked_stays})