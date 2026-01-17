from __future__ import annotations
from datetime import date
from typing import Optional

from sqlalchemy.orm import Query

from app.models.entities import Hotel


def apply_hotel_filters(
    q: Query,
    min_standard: Optional[int],
    require_wifi: Optional[bool],
    require_pool: Optional[bool],
    require_parking: Optional[bool],
) -> Query:
    if min_standard is not None:
        q = q.filter(Hotel.standard >= min_standard)

    if require_wifi is True:
        q = q.filter(Hotel.has_wifi.is_(True))
    if require_pool is True:
        q = q.filter(Hotel.has_pool.is_(True))
    if require_parking is True:
        q = q.filter(Hotel.has_parking.is_(True))

    return q


def nights_between(date_from: date, date_to: date) -> int:
    return max((date_to - date_from).days, 1)
