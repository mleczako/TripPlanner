from sqlalchemy.orm import Session
from datetime import date
from typing import Set

from app.models.entities import HotelAvailability


def get_available_hotels(
    db: Session,
    date_from: date,
    date_to: date,
    guests: int,
) -> Set[int]:
    availabilities = (
        db.query(HotelAvailability)
        .filter(
            HotelAvailability.is_available.is_(True),
            HotelAvailability.max_guests >= guests,
            HotelAvailability.date_from <= date_from,
            HotelAvailability.date_to >= date_to,
        )
        .all()
    )

    return {a.hotel_id for a in availabilities}
