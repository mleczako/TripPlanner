from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from database import get_db
from models.booking import Booking

router = APIRouter()

@router.get("/api/check-disruptions")
async def check_disruptions(db: Session = Depends(get_db)):
    count = db.query(Booking).filter(Booking.status == "disrupted").count()
    return {"disrupted_count": count}