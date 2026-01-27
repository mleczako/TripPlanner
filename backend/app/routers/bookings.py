from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.booking import Booking
from core.templates import templates

router = APIRouter()

@router.get("/bookings/{booking_id}/alternatives")
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

@router.post("/bookings/{original_id}/accept/{alt_id}")
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

@router.get("/booking/{booking_id}/change-success")
async def change_success_view(booking_id: int, request: Request, db: Session = Depends(get_db)):
    booking = db.query(Booking).get(booking_id)
    return templates.TemplateResponse(
        request,
        "change_success.html", 
        { "booking": booking}
    )
@router.post("/bookings/{booking_id}/cancel")
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

@router.post("/bookings/{booking_id}/keep")
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
        status_code=303
    )

@router.get("/booking/{booking_id}/risk")
def risk_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    b = db.query(Booking).get(booking_id)
    if not b:
        raise HTTPException(404)

    return templates.TemplateResponse(
        request,
        "risk_accept.html",
        { "booking": b}
    )

@router.get("/booking/{booking_id}/alternatives/view")
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
        request,
        "booking_alternatives.html",
        {
        
            "booking": booking,      
            "alternatives": alternatives
        }
    )

@router.get("/booking/{booking_id}/alert")
def booking_alert_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking or booking.status != "disrupted":
        return RedirectResponse("/my-bookings", status_code=303)

    return templates.TemplateResponse(
        request,
        "booking_alert.html",
        {
            
            "booking": booking
        }
    )
@router.get("/booking/{booking_id}/cancel/view")
def cancel_booking_view(
    booking_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).get(booking_id)
    if not booking:
        raise HTTPException(404)

    return templates.TemplateResponse(
        request,
        "booking_cancel.html",
        {
            
            "booking": booking
        }
    )

@router.get("/booking/{booking_id}/alternative/{alt_id}/details")
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
        request,
        "alternative_details.html", 
        {
            "booking": alt,      
            "original_id": booking_id
        }
    )