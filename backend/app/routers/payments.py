from fastapi import Depends, HTTPException, Request, APIRouter, Form
from services.payment_validator import validate_payment_details
import requests
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.booking import Booking
from core.templates import templates

router = APIRouter(prefix="/payment", tags=["Payments"])

@router.get("/{booking_id}")
async def payment_page(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404)
    
    if booking.status == "prepared":
        booking.status = "pending"
        db.commit()
    
    return templates.TemplateResponse("payment.html", {
        "request": request, 
        "booking": booking
    })

@router.post("/{booking_id}")
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
        return RedirectResponse(url=f"/details/{booking_id}", status_code=303)

   
    
    validation_error = validate_payment_details(paymentMethod, paymentToken)
    
    if validation_error:
        return templates.TemplateResponse("payment.html", {
            "request": request, 
            "booking": booking, 
            "error": validation_error
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