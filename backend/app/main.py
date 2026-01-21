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

from services.watchdog_service import watchdog_loop
import asyncio
from contextlib import asynccontextmanager
from models.event import Event

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(watchdog_loop())
    yield
  
app = FastAPI(lifespan=lifespan)
Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

def get_booked_count():
    db = SessionLocal()
    try:
        return db.query(Booking).filter(Booking.status == "booked").count()
    finally:
        db.close()

templates.env.globals.update(booked_count=get_booked_count)
from datetime import date
templates.env.globals.update(today=date.today().isoformat())

def validate_search_input(
    start_date: date | None,
    end_date: date | None,
    guests: int | None,
    budget: float | None,
    start_city: str | None
) -> str | None:
    if not start_date or not end_date:
        return "Data początkowa i końcowa są wymagane"
    if start_date< date.today():
        return "Daty podróży muszą być w przyszłości"
    if start_date >= end_date:
        return "Data końcowa musi być po dacie początkowej"

    if not guests or guests <= 0:
        return "Liczba gości musi być większa od zera"

    if not budget or budget <= 0:
        return "Budżet musi być większy od zera"

    if not start_city or start_city.strip() == "":
        return "Miejsce rozpoczęcia podróży jest wymagane"

    return None

from models.event import Event

def has_blocking_event(
    db: Session,
    city_name: str,
    start_date: date,
    end_date: date
):
    return db.query(Event).filter(
        Event.city == city_name,
        Event.date_from <= end_date,
        Event.date_to >= start_date,
        Event.severity.in_(["HIGH", "CRITICAL"])
    ).order_by(Event.severity.desc()).first()

@app.get("/")
@app.get("/results")
async def show_results(
    request: Request,
    startDate: date = None, endDate: date = None,
    guests: int = None, startCity: str = None, visitedCity: str = None,
    minPrice: float = 0, maxPrice: float = 100000,
    minRating: float = 0,
    wifi: int | None = None,
    pool: int | None = None,
    restaurant: int | None = None,

    db: Session = Depends(get_db)
):
    context = {"request": request, "bookings": [], "empty": False, "api_error": False}
    error = validate_search_input(
        startDate,
        endDate,
        guests,
        maxPrice,
        startCity
    )
    if startCity is not None:
        error = validate_search_input(startDate, endDate, guests, maxPrice, startCity)
        if error:
            context["error"] = error
            return templates.TemplateResponse("results.html", context)
    blocking_event = None

    if visitedCity and startDate and endDate:
        blocking_event = has_blocking_event(db, visitedCity, startDate, endDate)

    context["blocking_event"] = blocking_event

    if startDate and endDate and startCity:
        try:
           
            if visitedCity:
                generate_stay_proposals(
                    db, startDate, endDate, startCity, visitedCity, guests
                )
            else:
                all_cities = db.query(City).all()
                for city in all_cities:
                    generate_stay_proposals(
                        db, startDate, endDate, startCity, city.name, guests
                    )

        except ConnectionError:
            print("LOG: Wykryto awarię API!")
            context["api_error"] = True
            return templates.TemplateResponse("results.html", context)
        except Exception as e:
            print(f"LOG: Inny błąd API: {e}")

        start_city_obj = db.query(City).filter(func.lower(City.name) == startCity.lower()).first()
        visited_city_obj = db.query(City).filter(func.lower(City.name) == visitedCity.lower()).first()
        
        
        query = db.query(Booking).filter(
            Booking.status == "prepared",
            Booking.start_date == startDate,
            Booking.end_date == endDate,
            Booking.start_city_id == start_city_obj.id
        )

        if visitedCity:
            visited_city_obj = db.query(City).filter(
                func.lower(City.name) == visitedCity.lower()
            ).first()

            if not visited_city_obj:
                context["empty"] = True
                return templates.TemplateResponse("results.html", context)

            query = query.filter(
                Booking.visited_city_id == visited_city_obj.id
            )

        raw_bookings = query.all()

        print(f"[DEBUG] W bazie istnieje {len(raw_bookings)} ofert na tej trasie (przed filtracją ceny/osób).")

        valid_bookings = []
        for b in raw_bookings:
            if b.guests >= guests and minPrice <= b.total_price <= maxPrice and b.rating >= minRating and (wifi and b.hotel.has_wifi or wifi is None) and (pool and b.hotel.has_pool or pool is None) and (restaurant and b.hotel.has_restaurant or restaurant is None  ):
                b.is_risky = bool(blocking_event)
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
                    "items": [
                        f"hotel_{booking.hotel_id}",
                        f"flight_{booking.start_flight_id}",
                        f"flight_{booking.end_flight_id}"
                    ]
                }
                requests.post(f"{MOCK_API_URL}/external/finalize", json=confirm_payload)
                print("LOG: [KROK 10] Wysłano potwierdzenie rezerwacji do systemu zewnętrznego.")
            except Exception as e:
                print(f"LOG: Ostrzeżenie: Nie udało się wysłać potwierdzenia do API: {e}")

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
    from sqlalchemy.orm import joinedload 
    
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.visited_city)) 
        .filter(Booking.status.in_(["booked", "disrupted", "risk_accepted"]))
        .order_by(Booking.start_date)
        .all()
    )

    return templates.TemplateResponse(
        "booked.html",
        {
            "request": request,
            "bookings": bookings
        }
    )

@app.get("/bookings/{booking_id}/alternatives")
def get_alternatives(booking_id: int, db: Session = Depends(get_db)):
    original = db.query(Booking).get(booking_id)
    if not original:
        raise HTTPException(404, "Booking not found")
    if original.status != "disrupted":
        return []

    alts = db.query(Booking).filter(
        Booking.status == "prepared",
        Booking.parent_booking_id == original.id
    ).order_by(Booking.total_price.asc()).all()

    return alts

@app.post("/bookings/{original_id}/accept/{alt_id}")
async def accept_alternative(
    original_id: int, 
    alt_id: int, 
    db: Session = Depends(get_db)
):
    original = db.query(Booking).get(original_id)
    alternative = db.query(Booking).get(alt_id)

    if not original or not alternative:
        raise HTTPException(status_code=404, detail="Nie znaleziono rezerwacji")

    original.status = "cancelled"
  
    
    alternative.status = "booked"
    alternative.parent_booking_id = original.id

    db.commit()

    return RedirectResponse(url=f"/booking/{alternative.id}/change-success", status_code=303)

@app.get("/booking/{booking_id}/change-success")
async def change_success_view(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).get(booking_id)
    return templates.TemplateResponse(
        "change_success.html", 
        {"request": request, "booking": booking}
    )
@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise HTTPException(404)

    booking.status = "canceled"
    db.commit()

    return RedirectResponse("/my-bookings", status_code=303)

@app.post("/bookings/{booking_id}/keep")
def keep_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    b = db.query(Booking).get(booking_id)
    if not b:
        raise HTTPException(404)

    b.status = "risk_accepted"
    db.commit()

    return RedirectResponse(
        url="/my-bookings",
        stmatus_code=303
    )

@app.get("/booking/{booking_id}/risk")
def risk_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    b = db.query(Booking).get(booking_id)
    if not b:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "risk_accept.html",
        {"request": request, "booking": b}
    )

@app.get("/booking/{booking_id}/alternatives/view")
def alternatives_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise HTTPException(404)

    alternatives = db.query(Booking).filter(
        Booking.parent_booking_id == booking_id,
        Booking.status == "prepared"
    ).all()

    return templates.TemplateResponse(
        "booking_alternatives.html",
        {
            "request": request,
            "booking": booking,      
            "alternatives": alternatives
        }
    )

@app.get("/booking/{booking_id}/alert")
def booking_alert_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking or booking.status != "disrupted":
        return RedirectResponse("/my-bookings", status_code=303)

    return templates.TemplateResponse(
        "booking_alert.html",
        {
            "request": request,
            "booking": booking
        }
    )
@app.get("/booking/{booking_id}/cancel/view")
def cancel_booking_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "booking_cancel.html",
        {
            "request": request,
            "booking": booking
        }
    )

@app.get("/booking/{booking_id}/alternative/{alt_id}/details")
async def alternative_details(
    booking_id: int, 
    alt_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    original = db.query(Booking).get(booking_id)
    alt = db.query(Booking).get(alt_id)
    
    if not alt or alt.parent_booking_id != booking_id:
        raise HTTPException(status_code=404, detail="Alternatywa nie istnieje")

    return templates.TemplateResponse(
        "alternative_details.html", 
        {
            "request": request, 
            "booking": alt,      
            "original_id": booking_id
        }
    )
@app.get("/api/check-disruptions")
async def check_disruptions(db: Session = Depends(get_db)):
    count = db.query(Booking).filter(Booking.status == "disrupted").count()
    return {"disrupted_count": count}