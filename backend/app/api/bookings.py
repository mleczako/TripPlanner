from fastapi import APIRouter

router = APIRouter()


@router.get("/bookings")
def list_bookings():
    return {"bookings": []}
