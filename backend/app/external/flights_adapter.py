from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.models.entities import Flight


def get_outbound_flights(
    db: Session,
    from_airport: str,
    date_from: date,
    to_airport: str | None = None,
) -> List[Flight]:
    q = db.query(Flight).filter(
        Flight.from_airport == from_airport,
        Flight.date == date_from,
        Flight.status == "SCHEDULED",
    )

    if to_airport:
        q = q.filter(Flight.to_airport == to_airport)

    return q.all()


def get_return_flights(
    db: Session,
    to_airport: str,
    date_to: date,
) -> List[Flight]:
    return (
        db.query(Flight)
        .filter(
            Flight.to_airport == to_airport,
            Flight.date == date_to,
            Flight.status == "SCHEDULED",
        )
        .all()
    )
