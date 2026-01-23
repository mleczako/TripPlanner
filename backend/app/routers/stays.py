from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from database import get_db
from models.booking import Booking
from models.city import City
from services.stay_service import generate_stay_proposals
from sqlalchemy.orm import joinedload
from services.validators import validate_search_input
from services.alerts import has_blocking_event
from core.templates import templates
from services.stay_service import get_stays_number, get_total_saved_price

router = APIRouter()

@router.get("/")
@router.get("/results")
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
            Booking.status.in_(["prepared", "special"]),
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
    
    specials = db.query(Booking).filter(Booking.status.in_(["prepared", "special"])).limit(9).all()
    context["bookings"] = specials
    return templates.TemplateResponse("results.html", context)

@router.get("/details/{booking_id}")
async def get_details(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("details.html", {"request": request, "booking": booking})

@router.post("/book/{booking_id}")
async def confirm_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if booking:
        booking.status = "booked"
        db.commit()
    return RedirectResponse(url="/my-bookings", status_code=303)

@router.get("/my-bookings")
async def my_bookings(request: Request, db: Session = Depends(get_db)):

    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.visited_city))
        .filter(Booking.status.in_(["booked", "disrupted", "risk_accepted", "completed", "canceled"]))
        .order_by(Booking.start_date.desc())
        .all()
    )

    today = date.today()

    total_res, upcoming = get_stays_number(bookings, today)
    total_spent, total_saved = get_total_saved_price(bookings)

    return templates.TemplateResponse(
        "booked.html",
        {
            "request": request,
            "bookings": bookings,
            "stats": {
                "total": total_res,
                "upcoming": upcoming,
                "spent": round(total_spent, 2),
                "saved": round(total_saved, 2)
            },
            "today": today
        }
    )

@router.get("/special-offers")
async def special_offers(request: Request, db: Session = Depends(get_db)):
    special_bookings = (
        db.query(Booking)
        .filter(Booking.status == "special")
        .all()
    )
    
    return templates.TemplateResponse(
        "special_offers.html", 
        {
            "request": request, 
            "bookings": special_bookings,
            "empty": len(special_bookings) == 0
        }
    )