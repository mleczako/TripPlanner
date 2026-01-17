from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.entities import Hotel
from app.packages.stays.filter_service import apply_hotel_filters


def get_hotels(
    db: Session,
    locations: set[str],
    min_standard: Optional[int],
    require_wifi: Optional[bool],
    require_pool: Optional[bool],
    require_parking: Optional[bool],
) -> List[Hotel]:
    q = db.query(Hotel).filter(Hotel.location.in_(locations))

    q = apply_hotel_filters(
        q,
        min_standard,
        require_wifi,
        require_pool,
        require_parking,
    )

    return q.all()
